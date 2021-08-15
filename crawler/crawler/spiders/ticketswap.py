from ..items import EventItem, StatsItem
import scrapy
import re
import os
import sys
import time
import json
import pandas as pd
from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from crawler.database import locations



class TicketswapSpider(scrapy.Spider):
    name = 'ticketswap'

    def start_requests(self):
        '''Verzamelt links van de ticketswap event pagina'''
        platforms = {
            'linux' : '/usr/lib/chromium-browser/chromedriver',
            'win32' : r'C:\Users\SemKj\Downloads\chromedriver_win32\chromedriver'
        }
        options = Options()
        options.headless = True
        chromedriver = webdriver.Chrome(executable_path=platforms[sys.platform], options=options)

        chromedriver.get('https://www.ticketswap.nl/browse')

        urls = []
        for category in ['Festivals']:#, 'Clubavonden']: # zoek op type event # optioneel: 'Clubavonden'
            chromedriver.find_element(By.XPATH, '//h4[text()="Categorie"]').click()
            chromedriver.find_element(By.XPATH, f'//button[text()="{category}"]').click()
            for location in locations[:1]: # zoek op locatie uit database.py
                chromedriver.find_element(By.XPATH, '//h4[text()="Locatie"]').click()
                chromedriver.find_element(By.XPATH, '//input[@id="citysearch"]').clear()
                chromedriver.find_element(By.XPATH, '//input[@id="citysearch"]').send_keys(f'{location}')
                time.sleep(1)
                search_results = chromedriver.find_elements(By.XPATH, '//button[@class="css-yupldo ez685d2"]')
                search_results[0].click()
                time.sleep(1)

                # click 'laat meer zien'
                # klikt op de 'laat meer zien' knop tot alle evenementen vertoond worden
                while True:
                    try:
                        chromedriver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                        button = chromedriver.find_element(By.XPATH, '//h4[text()="Laat meer zien"]')
                        button.click()
                        time.sleep(1)
                    except:
                        break

                links = chromedriver.find_elements(By.XPATH, '//a[@role="link"]')
                for link in links:
                    url = link.get_attribute('href')
                    if url:
                        urls.append(url)


        chromedriver.close()
        print(f'\n{len(urls)} links found\n')
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_events)


    def parse_events(self, response):
        '''slaat event data op of verwijst door bij meerdere ticket_types'''
        item = EventItem()
        item['name'] = response.xpath('//h1/text()').get()
        item['platform'] = 'TS'
        location =  response.xpath('//p[@class="css-ickv75 e1gtd2336"]')
        item['location'], item['city'] = location.xpath('./a/text()').getall()
        item['country'] = location.xpath('./text()').getall()[-1][2:]
        item['event_date'] = response.xpath('//p[@class="css-ktbls8 e1gtd2335"]/text()').get()

        if 'Normaal' in response.xpath('//h2/text()').getall():
            item['url'] = response.url
            item['event_href'] = item['url'].split('/event/')[1].split('/')[0]
            item['ticket_href'] = item['event_href']
            yield item

            stats = StatsItem()
            stats['event_href'] = item['event_href']
            stats['ticket_href'] = item['event_href']
            stats['beschikbaar'] = response.xpath('//h6[contains(text(), "beschikbaar")]/preceding-sibling::span/text()').get()
            stats['verkocht'] = response.xpath('//h6[contains(text(), "verkocht")]/preceding-sibling::span/text()').get()
            stats['gezocht'] = response.xpath('//h6[contains(text(), "gezocht")]/preceding-sibling::span/text()').get()
            stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            stats['platform'] = 'TS'
            # zoekt de goedkoopst aangeboden ticketprijs als die er is
            price = response.xpath('//ul[preceding-sibling::h3[contains(text(), "Beschikbare tickets")]]//strong/text()').get()
            if price:
                stats['price'] = float(re.sub(r',', '.', re.sub(r'[^0-9,]', '', price)))
            # zoekt de ticketprijs van het meest recent verkochte ticket
            try:
                json_data = response.xpath('//script[@type="application/ld+json"]/text()').get()
                data = json.loads(json_data)
                id = data['itemListElement'][-1]['item']['@id'].split('/')[-1]
                payload = [{'operationName': "getSoldListings",
                    'query': "query getSoldListings($id: ID!, $first: Int, $after: String) {\n  node(id: $id) {\n    ... on EventType {\n      id\n      slug\n      title\n      soldListings: listings(\n        first: $first\n        filter: {listingStatus: SOLD}\n        after: $after\n      ) {\n        ...listings\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment listings on ListingConnection {\n  edges {\n    node {\n      ...listingList\n      __typename\n    }\n    __typename\n  }\n  pageInfo {\n    endCursor\n    hasNextPage\n    __typename\n  }\n  __typename\n}\n\nfragment listingList on PublicListing {\n  id\n  hash\n  description\n  isPublic\n  status\n  dateRange {\n    startDate\n    endDate\n    __typename\n  }\n  event {\n    id\n    name\n    startDate\n    endDate\n    slug\n    status\n    location {\n      id\n      name\n      city {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  eventType {\n    id\n    title\n    startDate\n    endDate\n    __typename\n  }\n  seller {\n    id\n    firstname\n    avatar\n    __typename\n  }\n  tickets(first: 99) {\n    edges {\n      node {\n        id\n        status\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  numberOfTicketsInListing\n  numberOfTicketsStillForSale\n  price {\n    originalPrice {\n      ...money\n      __typename\n    }\n    totalPriceWithTransactionFee {\n      ...money\n      __typename\n    }\n    sellerPrice {\n      ...money\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment money on Money {\n  amount\n  currency\n  __typename\n}\n",
                    'variables': {'id': id, 'first': 1}}]
                yield scrapy.Request('https://api.ticketswap.com/graphql/public/batch?flow=', callback=self.parse_json, method='POST', 
                    body=json.dumps(payload), headers={'Content-Type': 'application/json'}, meta={'stats': stats})
            except:
                yield stats
        else:
            ticket_types = response.xpath('//ul[@data-testid="event-types-list"]/li')
            for ticket in ticket_types:
                ticket_item = item.copy()
                link = ticket.xpath('./a/@href').get()
                yield scrapy.Request(link, callback=self.parse_tickets, meta={'item': ticket_item})



    def parse_tickets(self, response):
        item = response.meta['item']
        item['url'] = response.url
        item['event_href'] = item['url'].split('/event/')[1].split('/')[0]
        item['ticket_href'] = item['url'].split('/event/')[1].split('/')[1]
        yield item

        stats = StatsItem()
        stats['event_href'] = response.url.split('/event/')[1].split('/')[0]
        stats['ticket_href'] = response.url.split('/event/')[1].split('/')[1]
        stats['beschikbaar'] = response.xpath('//h6[contains(text(), "beschikbaar")]/preceding-sibling::span/text()').get()
        stats['verkocht'] = response.xpath('//h6[contains(text(), "verkocht")]/preceding-sibling::span/text()').get()
        stats['gezocht'] = response.xpath('//h6[contains(text(), "gezocht")]/preceding-sibling::span/text()').get()
        stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        stats['platform'] = 'TS'
        # zoekt de goedkoopst aangeboden ticketprijs als die er is
        price = response.xpath('//ul[preceding-sibling::h3[contains(text(), "Beschikbare tickets")]]//strong/text()').get()
        if price:
            stats['price'] = float(re.sub(r',', '.', re.sub(r'[^0-9,]', '', price)))
        # zoekt de ticketprijs van het meest recent verkochte ticket
        try:
            json_data = response.xpath('//script[@type="application/ld+json"]/text()').get()
            data = json.loads(json_data)
            id = data['itemListElement'][-1]['item']['@id'].split('/')[-1]
            payload = [{'operationName': "getSoldListings",
                'query': "query getSoldListings($id: ID!, $first: Int, $after: String) {\n  node(id: $id) {\n    ... on EventType {\n      id\n      slug\n      title\n      soldListings: listings(\n        first: $first\n        filter: {listingStatus: SOLD}\n        after: $after\n      ) {\n        ...listings\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment listings on ListingConnection {\n  edges {\n    node {\n      ...listingList\n      __typename\n    }\n    __typename\n  }\n  pageInfo {\n    endCursor\n    hasNextPage\n    __typename\n  }\n  __typename\n}\n\nfragment listingList on PublicListing {\n  id\n  hash\n  description\n  isPublic\n  status\n  dateRange {\n    startDate\n    endDate\n    __typename\n  }\n  event {\n    id\n    name\n    startDate\n    endDate\n    slug\n    status\n    location {\n      id\n      name\n      city {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  eventType {\n    id\n    title\n    startDate\n    endDate\n    __typename\n  }\n  seller {\n    id\n    firstname\n    avatar\n    __typename\n  }\n  tickets(first: 99) {\n    edges {\n      node {\n        id\n        status\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  numberOfTicketsInListing\n  numberOfTicketsStillForSale\n  price {\n    originalPrice {\n      ...money\n      __typename\n    }\n    totalPriceWithTransactionFee {\n      ...money\n      __typename\n    }\n    sellerPrice {\n      ...money\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment money on Money {\n  amount\n  currency\n  __typename\n}\n",
                'variables': {'id': id, 'first': 1}}]
            yield scrapy.Request('https://api.ticketswap.com/graphql/public/batch?flow=', callback=self.parse_json, method='POST', 
                body=json.dumps(payload), headers={'Content-Type': 'application/json'}, meta = {'stats': stats})
        except:
            yield stats

    def parse_json(self, response):
        try:
            data = json.loads(response.text)
            stats = response.meta['stats']
            stats['last_price'] = float(data[0]['data']['node']['soldListings']['edges'][0]['node']['price']['totalPriceWithTransactionFee']['amount']) / 100
            yield stats
        except:
            yield stats