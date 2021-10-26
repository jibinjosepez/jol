#!/usr/local/bin/python
# change above line to point to local
# python executable

import random
import traceback
import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import json 
import csv
import time

BASE_URL = "https://www.fiverr.com"

CATEGORY_URL = "categories"
CATEGORY_FILE = "./data/categories.json"
ALREADY_PARSED ="./data/alread_processed.json"
OUTPUT_FILE = "./data/output.csv"

def get_web_response (url, filter) :
    url = BASE_URL + url 
    print ('Getting Url: {}'.format(url))
    if (filter) :
        url = url + filter
    user_agent = ['PostmanRuntime/7.26.8', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.816', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0']

    retry = 0
    status = True
    while retry<=5:
        headers = {
                'User-Agent': random.choice(user_agent)
             }
        req = requests.get(url, headers=headers)
        if (req.status_code) == 403:
            print ('---------status_code--------------------', req.status_code)
            retry = retry+1
            time.sleep(30*retry)
    soup = BeautifulSoup(req.content, 'lxml')
    return soup, status


def parse_categories(url):
    output = {}
    results = get_web_response(url, None).find_all("section", class_="sitemap-box")
    for result in results:
        sections = result.find_all("ul")
        key1 = ""
        key2 = ""
        for sect in sections:
            lists = sect.find_all("li")
            for lis in lists:
                head = lis.find_all("h5")                
                if len(head) : 
                    striped =head[0].get_text()
                    key1 = striped
                    output[key1] = {}
                else :
                    striped = lis.get_text().strip()
                    if not striped.startswith('-') :
                        key2 = striped
                        output[key1][key2] = [(striped, lis.find('a')['href'])]
                    else : 
                        striped = striped.replace('-', '').strip()
                        output[key1][key2].append((striped, lis.find('a')['href']))

    return output

def parse_job(url, end) :
    try :
        soup = get_web_response(url, end).find_all("div", class_="gig-card-layout")
    except Exception as ex :
        print ('--------Exception--------', traceback.format_exc())
        return []
    output = []
    text = rate = price = None
    for result in soup:
        try:       
            text = result.find("h3", class_="text-display-7").find("a").get_text().strip()
        except Exception:
            pass
        try:
            rate = result.find("div", class_="rating-wrapper").find("span").get_text().strip()
        except Exception:
            pass
        try:       
            price = result.find("a", class_="price")['title'].strip()
        except Exception:
            pass
        output.append([text, rate, price])
    return output

def read_categories(file):
    category = {}
    with open(file) as json_file:
        category = json.load(json_file)
    return category

def write_categories(category, file):
    with open(file, 'w') as file:
        json.dump(category, file)

def get_categories() :
    category = []
    try : 
        category = read_categories(CATEGORY_FILE)
    except Exception :
        pass
    if not len(category) :
        category = parse_categories(CATEGORY_URL)
        write_categories (category, CATEGORY_FILE)
    return category

def parse_job_helper(url) :
    output = []
    # for page_id in range(1, 3) :
    page_id = 1
    end = "?source=toggle_filters&ref=pro%3Aany%7Csubscription%3Atrue&page=" + str(page_id)
    output.extend(parse_job(url, end))
    return output
# 
def get_already_parsed():
    lines = []
    with open(ALREADY_PARSED, 'r') as f:
        lines = f.read().splitlines()
    return lines

def update_already_parsed(item):
    with open(ALREADY_PARSED, 'a') as f:
        f.write("%s\n" % item)

def main () :
    print ("hi")
    categories = get_categories() 
    print ("categories parsed " + str(len(categories.keys())))
    already_parsed = []
    try : 
        already_parsed = get_already_parsed()
    except Exception :
        pass
    
    already_parsed = set(already_parsed)

    with open(OUTPUT_FILE, 'a') as f:
        writer = csv.writer(f)
        i = 100
        for key1, val in categories.items() :
            firstSkipped = False 
            for key2, val2 in val.items():
                for tuples in val2:
                    if len(val2) > 1 and not firstSkipped:
                        firstSkipped =  True
                        next
                    if  tuples[1] not in already_parsed :
                        output = parse_job_helper(tuples[1])
                        for dat in output :
                            row = [key1, key2, tuples[0], tuples[1]]
                            row.extend(dat)
                            writer.writerow(row)
                        already_parsed.add(tuples[1])
                        update_already_parsed(tuples[1])
                        time.sleep(5)

main()
