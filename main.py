from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
import time
import csv
import io
import sys
import requests
import pandas as pd
import numpy as np
import urllib3
from requests.exceptions import ConnectionError
from urllib3.exceptions import ProtocolError
from requests.exceptions import ChunkedEncodingError
import http
urllib3 .disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set path
base_ulr = "https://yellow.co.nz/new-zealand/elderly-care-%26-services?what=Elderly+Care+%26+Services&where=New+Zealand"
name_path = "//div[@class='title-container']//a/u"
phone_path = "//a[@data-ga-id='Phone_Number_Click_Primary']/span"
location_path = "//div[@class='servicing-areas-container']"
website_path = "//a[@data-ga-id='Website_Link']"


# Set browser
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")
options.binary_location = "/usr/bin/chromium"
driver = webdriver.Chrome('/usr/local/bin/chromedriver')

# clean cookies
cookies = driver.get_cookies()
driver.delete_all_cookies()


# loop all pages (from yellow.co.nz)
# Return: [[[{},{},...],[{},{},...],...],]
# all_pages->page->care_home->attr
def loop_all():
    all_pages = []

    while True:
        try:
            temp_page = get_current_page()
            all_pages.append(temp_page)

            # click NextPage button
            # next_button = driver.find_element_by_xpath("//button[@jsaction='pane.paginationSection.nextPage'][1]")
            btn_path = "//a[@class='btn btn-primary page-link pagination-next-page']"  # Next button path
            next_page_btn = driver.find_elements_by_xpath(btn_path)
            if len(next_page_btn) < 1:
                print("No more pages left")
                break
            else:
                WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, btn_path))).click()
        except ElementClickInterceptedException:
            break
    driver.quit()
    return all_pages


# get contact page url from website.
def get_contact_page(website):
    result = ''
    if website != '':
        if website.startswith("http"):
            part1 = website.split('://')  # split as ['protocol_name', 'domain']
            protocol = part1[0] + '://'
            domain = (part1[1].split('/'))[0]
            link = protocol+domain
        else:
            link = website.split('/')[0]

        urls = [link + '/contact', link + '/Contact', link + '/contacts', link + '/Contacts',
                link + '/contact-us',
                link + '/Contact-us', link + '/Contact-Us', link + '/contact-1', link + '/Contact-1']

        for url in urls:
            try:
                request = requests.get(url, verify=False)
                if request.status_code == 200:
                    result = url
                    return result
                    break
            except (http.client.HTTPException, ConnectionError, ProtocolError, ChunkedEncodingError):
                print()
    return result


# function to get all care home data for current page.
# Data structure: [{},{},...]
def get_current_page():
    result = []

    names = driver.find_elements_by_xpath(name_path)
    phones = driver.find_elements_by_xpath(phone_path)
    locations = driver.find_elements_by_xpath(location_path)
    websites = driver.find_elements_by_xpath(website_path)

    for i in range(len(names)):
        data = {
            "name": names[i].get_attribute('innerText'),
            "phone": handle_empty(names, phones, 'phones', i),
            "location": handle_empty(names, locations, 'locations', i),
            "website": handle_empty(names, websites, 'websites', i),
        }
        result.append(data)

    return result


# e.g. l1 is names; l2 is websites. (l1>l2 --- not all names have websites)
def handle_empty(l1, l2, ele, x):
    for i in range(len(l1)-len(l2)):
        l2.append('')

    if l2[x] == '':
        result = ''
    else:
        if ele == 'websites':
            result = l2[x].get_attribute('href')
        else:
            result = l2[x].get_attribute('innerText')
    return result


def get_email(website):
    driver_ = webdriver.Chrome('/usr/local/bin/chromedriver')
    if website.strip() == '':
        return ''
    else:
        contact_page = get_contact_page(website)
        email_path = "//a[starts-with(@href, 'mailto')]"

        if contact_page != '':
            driver_.get(contact_page)
            emails = driver.find_elements_by_xpath(email_path)
            email_set = set()
            for email in emails:
                temp = email.get_attribute('href')
                email_set.add(temp)
    driver_.quit()
    return email_set


# Main
driver.get(base_ulr)
all_data = loop_all()
# "email": get_email(websites[i].get_attribute('href')),
# Output
with open('output.csv', 'a') as f:  # Just use 'w' mode in 3.x
    f.write('name, phone, location, website, email\n')
    for page in all_data:
        for home in page:
            # home.update({'email': get_email(home.get('website'))})
            w = csv.DictWriter(f, home.keys())
            # w.writeheader()
            w.writerow(home)
    f.close()

table = pd.read_csv(r'output.csv')
emails_col = []
for page in all_data:
    for home in page:
        # emails_col.append(get_email(home.get('website')))
        print(get_contact_page(home.get('website')))
        # get_contact_page(home.get('website'))
# table['email'] = emails_col
# table.to_csv(r'output.csv', mode='a', index=False)

