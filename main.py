from flask import Flask, send_file
import pandas as pd
import time
from bs4 import BeautifulSoup

from selenium import webdriver
import chromedriver_binary  # Adds chromedriver binary to path
#from mysql_service import insert_day

app = Flask(__name__)



chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("window-size=1024,768")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options = chrome_options)


@app.route("/test")
def selenium_scraper():
    url = 'http://ido.xm.com.co/ido/SitePages/ido.aspx'
    sleep_time = 3

    driver.get(url)
    time.sleep(sleep_time)

    date = pd.to_datetime('today')

    date_box = driver.find_elements_by_id('report-date')
    date_box[0].clear()

    date_box[0].send_keys(date.strftime('%d/%m/%Y'))

    date_button = driver.find_elements_by_xpath('//div[@id="filter-button"]/button')
    date_button[0].click()
    time.sleep(sleep_time)

    #driver.save_screenshot("ido.png")
    #return send_file("ido.png")
        
    error = ''
    if 1==1:
        try:
            
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


            return 'Tables<p>'+ html_tables_no_open + '<p>Titles<p>'+ table_titles_string
        except Exception as e:
            error = str(e) 
    return error

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8080)