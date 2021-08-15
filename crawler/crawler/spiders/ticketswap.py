from ..items import EventItem, StatsItem
import scrapy
import re
import os
import sys
import time
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
            price = response.xpath('//ul[preceding-sibling::h3[contains(text(), "Beschikbare tickets")]]//strong/text()').get()
            if price:
                stats['price'] = float(re.sub(r',', '.', re.sub(r'[^0-9,]', '', price)))
            yield stats
        else:
            ticket_types = response.xpath('//ul[@data-testid="event-types-list"]/li')
            for ticket in ticket_types:
                ticket_item = item.copy()
                link = ticket.xpath('./a/@href').get()
                yield scrapy.Request(link, callback=self.parse_tickets, meta = {'item': ticket_item})



    def parse_tickets(self, response):
        stats = StatsItem()
        stats['event_href'] = response.url.split('/event/')[1].split('/')[0]
        stats['ticket_href'] = response.url.split('/event/')[1].split('/')[1]
        stats['beschikbaar'] = response.xpath('//h6[contains(text(), "beschikbaar")]/preceding-sibling::span/text()').get()
        stats['verkocht'] = response.xpath('//h6[contains(text(), "verkocht")]/preceding-sibling::span/text()').get()
        stats['gezocht'] = response.xpath('//h6[contains(text(), "gezocht")]/preceding-sibling::span/text()').get()
        stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        stats['platform'] = 'TS'
        price = response.xpath('//ul[preceding-sibling::h3[contains(text(), "Beschikbare tickets")]]//strong/text()').get()
        if price:
            stats['price'] = float(re.sub(r',', '.', re.sub(r'[^0-9,]', '', price)))
        yield stats

        item = response.meta['item']
        item['url'] = response.url
        item['event_href'] = item['url'].split('/event/')[1].split('/')[0]
        item['ticket_href'] = item['url'].split('/event/')[1].split('/')[1]
        yield item

