from flask import Flask, send_file
import pandas as pd
import time
from bs4 import BeautifulSoup

from selenium import webdriver
import chromedriver_binary  # Adds chromedriver binary to path
from sqlalchemy import create_engine
import sqlalchemy

app = Flask(__name__)



chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("window-size=1024,768")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options = chrome_options)

@app.route("/")
def app_root():
    return 'Funciona!'


@app.route("/xmscraper")
def xm_scraper():
    tables_raw, date = selenium_scraper()
    day_list = transform(tables_raw,date)
    df = pd.DataFrame(day_list)
    engine = create_engine('mysql+mysqldb://root:qju7lep86r1L4Nod@127.0.0.1:3306/xmdata', echo = False)
    df.to_sql(name = 'data_prepared', con = engine, if_exists = 'append', index = False)

    return 'Dia ' + str(date) + ' scrapiado'



@app.route("/pricescraper")
def price_scraper():
    price, date = price_selenium_scraper()

    day_price = {}

    day_price['date'] = date
    day_price['precio_bolsa_tx1'] = price

    prices_list = [day_price]

    df = pd.DataFrame(prices_list)

    engine = create_engine('mysql+mysqldb://root:qju7lep86r1L4Nod@127.0.0.1:3306/xmdata', echo = False)
    df.to_sql(name = 'prices', con = engine, if_exists = 'append', index = False)

    return 'Date: ' + str(date) + '\n' + 'Price: ' + price

def price_selenium_scraper():
    error = ''
    try:
        url = 'https://www.xm.com.co/Paginas/Home.aspx'
        sleep_time = 3

        driver.get(url)
        time.sleep(sleep_time)

        price_string = driver.find_elements_by_xpath('//div[@class="ax-home-marquee"]//ul[@id="ContenidoMarquesinaUno"]/li')[0].text

        price = price_string.split('$')[0].split(':')[1].replace(' ', '')

        date = pd.to_datetime('today')

        return price, str(date)
    except Exception as e:
        error = str(e) 
    return error

def selenium_scraper():
    error = ''
    try:
        url = 'http://ido.xm.com.co/ido/SitePages/ido.aspx'
        sleep_time = 3

        driver.get(url)
        time.sleep(sleep_time)

        date = pd.to_datetime('today')

        date_box = driver.find_elements_by_id('report-date')
        date_box[0].clear()

        date_box[0].send_keys(date.strftime('%Y/%m/%d'))

        date_button = driver.find_elements_by_xpath('//div[@id="filter-button"]/button')
        date_button[0].click()
        time.sleep(sleep_time)

        date_ido = driver.find_elements_by_xpath('//span[@id="fecha-reporte"]')[0].text

        #driver.save_screenshot("ido.png")
        #return send_file("ido.png")

        #Tables titles scraping

        scraped_table_titles = driver.find_elements_by_xpath('//div[@class="text-blue textL"]/b')

        scraped_table_titles.pop(0)

        table_titles_string = ''

        for table_title in scraped_table_titles:
            table_titles_string = table_titles_string + table_title.text + '|'


        tables = driver.find_elements_by_xpath('//table[@class="report-table"]')
        aportes_x = driver.find_elements_by_xpath('//table[@id="table-aportes-x"]/tbody')
        reservas_x = driver.find_elements_by_xpath('//table[@id="table-reservas-x"]/tbody')

        html_tables_no_open = ''

        for scraped_table in tables:

            if scraped_table.get_attribute('id') == 'table-aportes-x':
                if (aportes_x[0].get_attribute('innerHTML') != ''):
                    html_tables_no_open = html_tables_no_open + scraped_table.get_attribute('outerHTML') + '^_^'
                else:
                    pass
            elif scraped_table.get_attribute('id') == 'table-reservas-x':
                if (reservas_x[0].get_attribute('innerHTML') != ''):
                    html_tables_no_open = html_tables_no_open + scraped_table.get_attribute('outerHTML') + '^_^'
                else:
                    pass
            else:
                aportes_vacio = False
                reservas_vacio = False
                soup = BeautifulSoup(scraped_table.get_attribute('innerHTML'), 'lxml')
                td = soup.find('td')
                tbody = soup.find('tbody')
                #print(td)
                if str(td)== '<td>Rio</td>':
                    if str(tbody) == '<tbody class="report-table-body"></tbody>':
                        aportes_vacio = True
                        print('Entra aportes_vacio')
                if str(td)== '<td> Embalse </td>':
                    if str(tbody) == '<tbody class="report-table-body"></tbody>':
                        reservas_vacio = True
                        print('entra reservas vacio')
                    
                if aportes_vacio:
                    pass
                elif reservas_vacio:
                    pass
                else:
                    html_tables_no_open = html_tables_no_open + scraped_table.get_attribute('outerHTML') + '^_^'

        return html_tables_no_open, date
    except Exception as e:
        error = str(e) 
    return error


def transform(tables_raw, date):
   
    days_list = []
    
    t_raw = tables_raw.split('^_^')

    day_dict = {}
    day_dict['date'] = date


    # 0. Generacion

    try:
        generacion = pd.read_html(t_raw[0], index_col=0)[0]
        day_dict['generacion_total_programada_redespacho'] = generacion.loc['GENERACION'].loc['Programada Redespacho (GWh)']
        day_dict['generacion_total_programada_despacho'] = generacion.loc['GENERACION'].loc['Programada Despacho (GWh)']
        day_dict['generacion_total_real'] = generacion.loc['GENERACION'].loc['Real (GWh)']
    except:
        day_dict['generacion_total_programada_redespacho'] = 'ND'
        day_dict['generacion_total_programada_despacho'] = 'ND'
        day_dict['generacion_total_real'] = 'ND'
        print(f'Error en generacion el dia: {date}')
        
        

    # 1. Intercambios internacionales
    try:
        intercambios_internacionales = pd.read_html(t_raw[1], index_col=0)[0]
        day_dict['importacion_programada_redespacho'] = intercambios_internacionales.loc['Importaciones'].loc['Programada Redespacho (GWh)']
        day_dict['importacion__real'] = intercambios_internacionales.loc['Importaciones'].loc['Real (GWh)']
        day_dict['exportacion_programada_redespacho'] = intercambios_internacionales.loc['Exportaciones'].loc['Programada Redespacho (GWh)']
        day_dict['exportacion__real'] = intercambios_internacionales.loc['Exportaciones'].loc['Real (GWh)']
    except:
        day_dict['importacion_programada_redespacho'] = 'ND'
        day_dict['importacion__real'] = 'ND'
        day_dict['exportacion_programada_redespacho'] = 'ND'
        day_dict['exportacion__real'] = 'ND'
        print(f'Error en intercambios internacionales el dia: {date}')
        
        
    # 2. Disponibilidad
    try:
        disponibilidad = pd.read_html(t_raw[2], index_col=0)[0]
        day_dict['disponibilidad_real'] = disponibilidad.loc['DISPONIBILIDAD'].loc['Real (MW)']
    except:
        day_dict['disponibilidad_real'] = 'ND'
        print(f'Error en disponibilidad el dia: {date}')
        
        
    # 3. Demanda no atendida
    try:
        demanda_no_atendida = pd.read_html(t_raw[3], index_col=0)[0]
        day_dict['demanda_no_atendida'] = demanda_no_atendida.loc['Total Demanda no atendida -SIN-'].loc['MWh']
    except:
        day_dict['demanda_no_atendida'] = 'ND'
        print(f'Error en demanda no atendida el dia: {date}')
        
        
    # 7. Costos
    try:
        demanda_no_atendida = pd.read_html(t_raw[7], index_col=0)[0]
        day_dict['costo_marginal_promedio_redespacho'] = demanda_no_atendida.loc['Costo Marginal Promedio del Redespacho ($/kWh)'].loc['$/kWh']
    except:
        day_dict['costo_marginal_promedio_redespacho'] = 'ND'
        print(f'Error en costo marginal promedio el dia: {date}')
        
    # 8. Aportes
    try:
        aportes = pd.read_html(t_raw[9], index_col=0)[0]
        indices = aportes.index

        indice_aportes = ''
        columna_aportes = ''

        for indice in indices:
            if str(indice) == 'TOTAL -SIN-':
                indice_aportes = 'TOTAL -SIN-'
                columna_aportes = 'GWh'
            elif str(indice) == 'Total SIN':
                indice_aportes = 'Total SIN'
                columna_aportes = "Caudal GWh"
                
        day_dict['aportes_hidricos'] = aportes.loc[indice_aportes].loc[columna_aportes]
    except:
        day_dict['aportes_hidricos'] = "ND"
        print(f'Error en aportes el dia: {date}')
        
    # 9. Reservas
    try:
        
        reservas = pd.read_html(t_raw[10], index_col=0)[0]
        
        indices = reservas.index

        indice_reservas = ''
        columna_reservas = ''

        for indice in indices:
            if str(indice) == 'TOTAL -SIN-':
                indice_reservas = 'TOTAL -SIN-'

            elif str(indice) == 'Total SIN':
                indice_reservas = 'Total SIN'



        columnas = reservas.columns

        for columna in columnas:
            if str(columna) == 'Volumen Util Diario GWh':
                columna_reservas_1 = 'Volumen Util Diario GWh'
            elif str(columna) == 'Volumen Util Diario GWh(1)':
                columna_reservas_1 = 'Volumen Util Diario GWh(1)'

        for columna in columnas:
            if str(columna) == 'Volumen GWh':
                columna_reservas_2 = 'Volumen GWh'
            elif str(columna) == 'Volumen GWh(4)':
                columna_reservas_2 = 'Volumen GWh(4)'


        day_dict['volumen_util_diario'] = reservas.loc[indice_reservas].loc[columna_reservas_1]
        day_dict['volumen'] = reservas.loc[indice_reservas].loc[columna_reservas_2]
        
    except:
        day_dict['volumen_util_diario'] = 'ND'
        day_dict['volumen'] = 'ND'
        print(f'Error en volumen: {date}')
    
    days_list.append(day_dict)
    
    return days_list
