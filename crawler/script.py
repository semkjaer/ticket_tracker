#!/usr/bin/python

import os

spiders = os.popen('scrapy list').read()
for spider in spiders.split('\n'):
    if spider:
        os.system(f'scrapy crawl {spider}')
