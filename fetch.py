"""Copied from "an introduction to compassionate screenscraping"
http://dev.lethain.com/an-introduction-to-compassionate-screenscraping/
Implements local caching for URLs and spaces out requests to same domain
to 1 req per 1.1 seconds (tweakable). Uses httplib2 library for caching."""

import httplib2
import time
import re

SCRAPING_CONN = httplib2.Http(".cache")
SCRAPING_DOMAIN_RE = re.compile("\w+:/*(?P<domain>[a-zA-Z0-9.]*)/")
SCRAPING_DOMAINS = {}
SCRAPING_CACHE_FOR = 60 * 15 # cache for 15 minutes
SCRAPING_REQUEST_STAGGER = 600 # in milliseconds
SCRAPING_CACHE = {}

def fetch(url,method="GET"):
    key = (url,method)
    now = time.time()
    if SCRAPING_CACHE.has_key(key):
        data,cached_at = SCRAPING_CACHE[key]
        if now - cached_at < SCRAPING_CACHE_FOR:
            return data
    domain = SCRAPING_DOMAIN_RE.findall(url)[0]
    if SCRAPING_DOMAINS.has_key(domain):
        last_scraped = SCRAPING_DOMAINS[domain]
        elapsed = now - last_scraped
	if elapsed < SCRAPING_REQUEST_STAGGER:
	    wait_period = (SCRAPING_REQUEST_STAGGER - elapsed) / 1000
            time.sleep(wait_period)
    SCRAPING_DOMAINS[domain] = time.time()
    data = SCRAPING_CONN.request(url,method)
    SCRAPING_CACHE[key] = (data,now)
    return data