from ..items import EventItem, StatsItem
import scrapy
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
        options = Options()
        # options.headless = True
        chromedriver = webdriver.Chrome(executable_path=r'C:\Users\SemKj\Downloads\chromedriver_win32\chromedriver', options=options)
        chromedriver.get('https://www.ticketswap.nl/browse')

        urls = []
        for category in ['Festivals']:#, 'Concerten', 'Clubavonden']: # zoek op type event
            chromedriver.find_element(By.XPATH, '//h4[text()="Categorie"]').click()
            chromedriver.find_element(By.XPATH, f'//button[text()="{category}"]').click()
            for location in locations[:2]: # zoek op locatie
                chromedriver.find_element(By.XPATH, '//h4[text()="Locatie"]').click()
                chromedriver.find_element(By.XPATH, '//input[@id="citysearch"]').clear()
                chromedriver.find_element(By.XPATH, '//input[@id="citysearch"]').send_keys(f'{location}')
                time.sleep(1)
                search_results = chromedriver.find_elements(By.XPATH, '//button[@class="css-yupldo ez685d2"]')
                search_results[0].click()
                time.sleep(1)

                # click 'laat meer zien'
                # klikt op de 'laat meer zien' knop tot alle evenementen vertoond worden
                # while True:
                #     try:
                #         chromedriver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                #         button = chromedriver.find_element(By.XPATH, '//h4[text()="Laat meer zien"]')
                #         button.click()
                #         time.sleep(1)
                #     except:
                #         break

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
        location =  response.xpath('//p[@class="css-ickv75 e1gtd2336"]')
        item['location'], item['city'] = location.xpath('./a/text()').getall()
        item['country'] = location.xpath('./text()').getall()[-1][2:]


        if 'Beschikbare tickets' in response.xpath('//h3/text()').getall():
            item['event_href'] = response.url.split('/event/')[1].split('/')[0]
            item['ticket_href'] = item['event_href']
            yield item

            stats = StatsItem()
            item['event_href'] = item['event_href']
            item['ticket_href'] = item['event_href']
            stats['beschikbaar'] = response.xpath('//h6[contains(text(), "beschikbaar")]/preceding-sibling::span/text()').get()
            stats['verkocht'] = response.xpath('//h6[contains(text(), "verkocht")]/preceding-sibling::span/text()').get()
            stats['gezocht'] = response.xpath('//h6[contains(text(), "gezocht")]/preceding-sibling::span/text()').get()
            stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            stats['platform'] = 'TS'
            yield stats
        
        else:
            ticket_types = response.xpath('//ul[@data-testid="event-types-list"]/li')
            for ticket in ticket_types:
                ticket_item = item.copy()
                link = ticket.xpath('./a/@href').get()
                yield scrapy.Request(link, callback=self.parse_tickets, meta = {'item': ticket_item})



    def parse_tickets(self, response):
        item = response.meta['item']
        stats = StatsItem()
        stats['event_href'] = response.url.split('/event/')[1].split('/')[0]
        stats['ticket_href'] = response.url.split('/event/')[1].split('/')[1]
        stats['beschikbaar'] = response.xpath('//h6[contains(text(), "beschikbaar")]/preceding-sibling::span/text()').get()
        stats['verkocht'] = response.xpath('//h6[contains(text(), "verkocht")]/preceding-sibling::span/text()').get()
        stats['gezocht'] = response.xpath('//h6[contains(text(), "gezocht")]/preceding-sibling::span/text()').get()
        stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        stats['platform'] = 'TS'
        yield stats

        url = response.url
        item['event_href'] = url.split('/event/')[1].split('/')[0]
        item['ticket_href'] = url.split('/event/')[1].split('/')[1]
        yield item

