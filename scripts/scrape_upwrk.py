#!/usr/local/bin/python
# change above line to point to local
# python executable

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
    if (filter) :
        url = url + filter
    print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage)
    return soup

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
        if ex.status == 403:
            print ("Error")
            raise ex
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
    for page_id in range(1, 3) :
        end = "?source=toggle_filters&ref=pro%3Aany%7Csubscription%3Atrue&page=" + str(page_id)
        output.extend(parse_job(url, end))
    return output

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

    f = open(OUTPUT_FILE, 'a')
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
                        row = [key1, key2, tuples[1]]
                        row.extend(dat)
                        writer.writerow(row)
                    already_parsed.add(tuples[1])
                    update_already_parsed(tuples[1])
                    time.sleep(60)
    f.close()

main()
