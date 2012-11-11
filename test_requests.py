import csv
import requests
import re
import codecs
from BeautifulSoup import BeautifulSoup
import cStringIO

class DictUnicodeWriter(object):

    def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, D):
        self.writer.writerow({k:unicode(v).encode("utf-8") for k,v in D.items()})
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for D in rows:
            self.writerow(D)

    def writeheader(self):
        self.writer.writeheader()

def parse_rest(rest_str):
    rest_soup = BeautifulSoup(rest_str)

    lat = float(rest_str.split(",")[0])
    lon = float(rest_str.split(",")[1])

    rest_addr_list = rest_soup.find("div").contents
    rest_name = rest_soup.find("a").contents[0].encode("utf-8",'ignore')


    rest_street = rest_addr_list[0].replace("\\n","")
    rest_town = rest_addr_list[-1].split(", ")[0].replace("\\n","")
    rest_state = rest_addr_list[-1].split(" ")[1]
    rest_pcode = rest_addr_list[-1].split(" ")[-1].replace("\\n","")

    try:
        rest_rating = int(rest_soup.find("span").contents[0][:-1])
    except AttributeError:
        rest_rating = None ## Could be an issue; better to be 0?


    rest_as_dict = {
        "name": rest_name,
        "street": rest_street,
        "town": rest_town,
        "state": rest_state,
        "postcode": rest_pcode,
        "rating": rest_rating,
        "lat": lat,
        "lon": lon
        }
    return rest_as_dict


def extract_restaurants(page_url):
    print "currently trying " + page_url
    r = requests.get(page_url)
    
    soup = BeautifulSoup(r.text, fromEncoding="utf-8")
    
    objs = soup.find(text=re.compile("cR"))
    rests = (x for x in objs.split("cR(") if not x.startswith("\nfunction"))
    restlist = [parse_rest(x) for x in rests]

    if not soup.find("span","disabled next_page"):
        next_page = "http://www.urbanspoon.com" + soup.find("a","next_page")['href']
        print "about to try " + next_page
        restlist += extract_restaurants(next_page)
        return restlist
    else:
        return restlist

def WriteToCSV(dictlist,filename):
    """Writes the restaurant dict list to csv. Note hardcoded field order"""
    # fields in desired order. could remove & write header line another way
    # if we don't care about the order.
    fields = ["name","rating","street","town","state","postcode","lat","lon"]
    # write it out to a csv
    # outf = codecs.open(filename,"wb",encoding="utf-8",errors="replace")
    outf = open(filename,"wb")
    dw = DictUnicodeWriter(outf,fields)
    dw.writerow(dict((fn,fn) for fn in fields)) # header row
    # for D in dictlist:
    #    dw.writerow({k:v.encode('utf8') for k,v in D.items()})
    dw.writerows(dictlist)
    outf.close()
    return None

rest_list_url = "http://www.urbanspoon.com/g/71/5907/Victoria/Melbourne-Northern-Suburbs-restaurants"

coburg_url = "http://www.urbanspoon.com/n/71/47207/Melbourne/Coburg-restaurants"

bad_url = "http://www.urbanspoon.com/g/71/5907/Melbourne/Northern-Suburbs-restaurants?page=16"

big_rest_list = extract_restaurants(bad_url)

WriteToCSV(big_rest_list,"bad.csv")
