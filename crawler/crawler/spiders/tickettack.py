from ..items import EventItem, StatsItem
import scrapy
import json
from datetime import date, datetime


class TicketswapSpider(scrapy.Spider):
    name = 'tickettack'
    start_urls = ['https://www.tickettack.nl//nl/evenementen&readPopup=true']

    def parse(self, response):
        events = response.xpath('//li[contains(@onclick, "location.href=")]')
        for event in events:
            item = EventItem()
            item['name'] = event.xpath('.//h3/text()').get()
            info = event.xpath('.//p/text()').get().split(',')
            item['event_date'] = info[0]
            item['location'] = info[1].strip()
            item['city'] = info[2].strip()
            item['event_href'] = event.attrib['onclick'].split("'")[1]
            url = 'https://www.tickettack.nl//nl/' + item['event_href']
            yield scrapy.Request(url, callback=self.parse_event, meta={'item': item})
        
        load_more = response.xpath('//a[@onclick="moreEvents()"]')
        if load_more and 'block' in load_more.xpath('./@style').get():
            yield scrapy.Request('https://www.tickettack.nl//nl/evenementen&readPopup=true', 
                                    callback=self.parse,
                                    method='POST',
                                    body="{ 'more': '1', 'ajax': '1' }")


    def parse_event(self, response):
        item = response.meta['item']
        ticket_data = response.xpath('//article[@class="monthpassBox"]/ul/li')
        if ticket_data:
            stats = StatsItem()
            stats['event_href'] = response.url.split('/nl/')[1].split('/')[0]
            stats['ticket_href'] = response.url.split('/nl/')[1].split('/')[0]
            stats['beschikbaar'] = ticket_data.xpath('./cite[contains(text(), "Aangeboden")]/following-sibling::span/text()').get()
            stats['gezocht'] = ticket_data.xpath('./cite[contains(text(), "Verkocht")]/following-sibling::span/text()').get()
            stats['verkocht'] = ticket_data.xpath('./cite[contains(text(), "Gezocht")]/following-sibling::span/text()').get()
            stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            stats['platform'] = 'TT'
            yield stats

            item['ticket_href'] = item['event_href']
            yield item
        else:
            for ticket in response.xpath('//ul[@id="loadingTickets"]/li'):
                ticket_item = item.copy()
                link =  ticket.attrib['onclick'].split("'")[1]
                ticket_item['ticket_href'] = link.split('/nl/')[1].split('/')[1]
                yield ticket_item
                yield scrapy.Request(link, callback=self.parse_tickets)
                

    def parse_tickets(self, response):
        stats = StatsItem()
        stats['event_href'] = response.url.split('/nl/')[1].split('/')[0]
        stats['ticket_href'] = response.url.split('/nl/')[1].split('/')[1]
        stats['beschikbaar'] = response.xpath('./cite[contains(text(), "Aangeboden")]/following-sibling::span/text()').get()
        stats['gezocht'] = response.xpath('./cite[contains(text(), "Verkocht")]/following-sibling::span/text()').get()
        stats['verkocht'] = response.xpath('./cite[contains(text(), "Gezocht")]/following-sibling::span/text()').get()
        stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        stats['platform'] = 'TT'
        yield stats
