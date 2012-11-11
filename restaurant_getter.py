import re
import csv
from fetch import fetch
from BeautifulSoup import BeautifulSoup

def ParseRestaurant(rest_page_url):
	"""Parses an UrbanSpoon restaurant page for the name, rating, and
	address of the restaurant. Text values are encoded to UTF8 from unicode
	for writing to CSV post-hoc. Note that HTML class names etc. may change."""
	page = fetch(rest_page_url)
	try:
		soup = BeautifulSoup(page[1])
		name = soup.findAll('h1','page-title fn org')[0].text.encode("utf8")
		print "looking at %s"%name
	
		## Address info
		street_addr = soup.findAll('span','street-address')[0].text.encode("utf8")
		suburb = soup.findAll('span','locality')[0].text.encode("utf8")
		postcode = soup.findAll('a','quiet-link postal-code')[0].text.encode("utf8")
	
		## Number of votes
		try:
			num_voted = int(soup.findAll('div',id='num-votes')[0].text.split(" ")[0])
		except ValueError:
			num_voted = 0
	
		## Rating - if restaurant hasn't been rated, there isn't a span of than name
		## And if there is, there might be something Weird
		try:
			rating = soup.findAll('span','percent-text rating average')[0].text
			rating_as_num = int(rating[:-1]) # knock off the % sign
		except (ValueError,IndexError):
			rating_as_num = 0
			
		rest_details = {"name":name,
						"street":street_addr,
						"suburb":suburb,
						"postcode":postcode,
						"number_voted":num_voted,
						"rating":rating_as_num,}
		return rest_details
	except IndexError:
		return {}

def ReadRestaurants(url):
	"""Gets the details for restaurants on an UrbanSpoon page. Uses
	the built-in google map to extract the locations of each restaurant."""
	page = fetch(url)
	soup = BeautifulSoup(page[1])
	
	## Get the details for the restaurants on this table by going into their page
	rest_table = soup.findAll("table",id="r-t")[0] # r-t is the id of the restaurants
	rests = rest_table.findAll("div","t") # class "t" holds the restaurant entries
	links_to_rests = [r.findAll("a",href=True)[0] for r in rests] # valid entries have a link in the href
	## go get the restaurants
	rest_dicts = [ParseRestaurant(x['href']) for x in links_to_rests]
	
	## Get the lat/lons out of the map on the link page
	scripts = soup.findAll("script")
	map_script = scripts[-4] ## No idea if it will always be the 4th-last one
	
	# regex for lat, lon pairs in text
	lat_lon_re = re.compile("-?[0-9]{1,2}.[0-9]+, -?[0-9]{1,3}.[0-9]+")
	# list of them. they will be in alphabetical order, same as the rest dicts
	rest_lat_lons = [x.split(", ") for x in lat_lon_re.findall(map_script.text)]
	# which means we can just zip them up and append the locations to the restaurant dict
	for restaurant,location in zip(rest_dicts,rest_lat_lons):
		restaurant["lat"] = float(location[0])
		restaurant["lon"] = float(location[1])

	return rest_dicts

def FillSubsequentPages(base):
	## Get the restaurants for this page
	rests = ReadRestaurants(base)

	## Are there any pages after this?
	page = fetch(base)
	soup = BeautifulSoup(page[1])
	try:
		next_page_tag = [pg for pg in soup.findAll('a') if "next page" in pg.text][0]
	except IndexError:
		next_page_tag = False
	## If so:
	if next_page_tag:
		## Tell it what the proper URL is
		next_page_url = "http://www.urbanspoon.com" + next_page_tag['href']
		## And get the restaurants on that page too
		rests = rests + FillSubsequentPages(next_page_url)
		return rests
	else:
		return rests
	
def WriteToCSV(dictlist,filename):
	"""Writes the restaurant dict list to csv. Note hardcoded field order"""
	# fields in desired order. could remove & write header line another way
	# if we don't care about the order.
	fields = ["name","rating","number_voted","street","suburb","postcode","lat","lon"]
	# write it out to a csv
	outf = file(filename,"wb")
	dw = csv.DictWriter(outf,fields)
	dw.writerow(dict((fn,fn) for fn in fields)) # header row
	dw.writerows(dictlist)
	outf.close()
	return None

restaurant_list = \
	"http://www.urbanspoon.com/n/71/47146/Melbourne/Northcote-restaurants"

testrests = FillSubsequentPages(restaurant_list)
WriteToCSV(testrests,"NorthernSuburbs.csv")
