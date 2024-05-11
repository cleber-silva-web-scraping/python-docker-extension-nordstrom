import undetected_chromedriver as uc
import requests
import json
from lxml import html
import datetime
import time
import csv
import os.path
import os
import random

from dotenv import load_dotenv
load_dotenv()

from core.sendgrid import send_email
from core.telegram import send_message
from core.zipfile import compact_file

cookies = {}
headers = {}

def get_variables():
    global headers, cookies
    cookies = {}
    headers = {}
    url = f'https://www.nordstrom.com/brands/la-femme--5309?origin=productBrandLink&page=1'
    bloqued_url = 'https://siteclosed.nordstrom.com/invitation.html'
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    max_try = 5
    while max_try > 0:
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--auto-open-devtools-for-tabs");
        #options.add_argument(f"--user-agent={user_agent}")
        driver = uc.Chrome(options=options)
        driver.get(url)
        time.sleep(2)
        max_refresh = 5 
        while driver.current_url == bloqued_url and max_refresh > 0:
            time.sleep(random.randint(3, 8))
            driver.get(url)
            time.sleep(2)
            print('Blocked....')
            max_refresh = max_refresh - 1

        if driver.current_url == bloqued_url:
            print('Restart browser...')
            driver.quit()
            max_try = max_try - 1
            time.sleep(random.randint(3, 8))

        else:
            driver.refresh()
            time.sleep(1)
            user_agent = driver.execute_script("return navigator.userAgent;")
            user_cookie = driver.execute_script("return document.cookie;")
            cookies = {'cookies': user_cookie}
            headers = {'user-agent': user_agent }
            driver.quit()
            return 
    print('Fatal blocked page...')
    exit(0)


def extract_data(link):
    data = []
    response = requests.get(link, cookies=cookies, headers=headers)
    tree = html.fromstring(response.content)
    body_json = json.loads(tree.xpath("/html/body/script[1]/text()")[0].replace('window.__INITIAL_CONFIG__ = ',''))
    try:
        prices_by_sku = body_json['viewData']['price']['bySkuId']
    except:
        prices_by_sku = None

    skus = body_json['viewData']['skus']['byId']
    features = body_json['viewData']['features']
    Review_Stars = body_json['viewData']['reviews']['averageRating']
    Review_Count = body_json['viewData']['reviews']['numberOfReviews']
    productName = body_json['viewData']['productName']

    if len(skus) == 0:
        tmp = {
                'URL': link,
                'SKU': 'N/A',
                'Item#': features[-1].split('#')[-1],
                'Title': productName,
                'Color': 'N/A',
                'Size': 'N/A',
                'Available_QTY': 'N/A',
                'Available': 'Not available',
                'Date': datetime.date.today().isoformat(),
                'Currency': 'USD',
                'Price': 999,
                'Review_Count': Review_Count,
                'Review_Stars': Review_Stars,
        }
        print(tmp)
        data.append(tmp)
    else:
        for sku in skus:
            if prices_by_sku == None:
                currencyCode = 'USD'
                price = 'SOULD OUT'
            else:
                currencyCode = prices_by_sku[sku]['regular']['price']['currencyCode']
                price = f"{prices_by_sku[sku]['regular']['price']['units']}."
                price = f"{price}{prices_by_sku[sku]['regular']['price']['nanos']}"

            if skus[sku]['totalQuantityAvailable'] == 0:
                available = f"Not available in {skus[sku]['colorDisplayValue']}"
            elif skus[sku]['totalQuantityAvailable'] == 1:
                available = 'Only 1 left'
            elif skus[sku]['totalQuantityAvailable'] == 2:
                available = 'Only 2 left'
            elif skus[sku]['totalQuantityAvailable'] < 6:
                available = 'Only a few left'
            else:
                available = 'In Stock'

            tmp = {
                'URL': link,
                'SKU': sku,
                'Item#': features[-1].split('#')[-1],
                'Title': productName,
                'Color': skus[sku]['colorDisplayValue'],
                'Size': skus[sku]['sizeDisplayValue'],
                'Available_QTY': skus[sku]['totalQuantityAvailable'],
                'Available': available,
                'Date': datetime.date.today().isoformat(),
                'Currency': currencyCode,
                'Price': price,
                'Review_Count': Review_Count,
                'Review_Stars': Review_Stars,
            }
            print(tmp)
            data.append(tmp)
    time.sleep(10)
    return data

def get_detail():    
    f_name = f"{os.getenv('PATH_RESULT')}nordstrom_{datetime.date.today().isoformat()}.csv"
    head_lines = os.path.isfile(f_name)
    f = open(f"{os.getenv('PATH_RESULT')}toDo.txt", "r")
    lines = f.read().split('\n')
    f.close()
    while len(lines) > 0:
        line = lines.pop()
        if line != '':
            try:
                row = extract_data(line)
                if len(row) > 0:
                    with open(f_name, 'a') as f:
                        writer = csv.DictWriter(f, fieldnames=row[0])
                        if head_lines == False:
                            head_lines = True
                            writer.writeheader()
                        writer.writerows(row)
                else:
                    with open(f"{os.getenv('PATH_RESULT')}no_records_found.txt", 'a') as f:
                        f.write(f'{line}\n')

                with open(f"{os.getenv('PATH_RESULT')}toDo.txt", 'w') as f:
                    for link in lines:
                        f.write(f'{link}\n')
            except Exception as e:
                print(e)
                lines.append(line)
                time.sleep(10)
                get_variables()
    return f_name

def get_links():
    page=1
    with open(f"{os.getenv('PATH_RESULT')}toDo.txt", 'w') as f:
        while True: 
            print('Buscando  urls...')
            time.sleep(2)
            url = f'https://www.nordstrom.com/brands/la-femme--5309?origin=productBrandLink&page={page}'
            response = requests.get(url, cookies=cookies, headers=headers)
            tree = html.fromstring(response.content)
            header = tree.xpath("//main//header//span")
            if len(header) == 0:
                get_variables()
            else:
                articles = tree.xpath("//article")
                links = [f"https://www.nordstrom.com{article.xpath('h3/a/@href')[0]}" for article in articles]
                if(len(links) == 0):
                    break
                print(url)
                for link in links:
                    f.write(f'{link}\n')
                page = page + 1

if __name__ == '__main__':
    send_message(f"Start Nordstrom process...")
    get_links()
    f_name = get_detail()
    compacted_file = compact_file(f_name)
    send_email(
        os.getenv('EMAIL_TO'),
        f"Data updated [{f_name.split('/')[-1]}]",
        '<strong>Data from web site Nordstrom</strong>',
        compacted_file)

    send_message(f"File sent: {f_name.split('/')[-1]}.")


