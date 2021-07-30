from ..items import EventItem, StatsItem
import scrapy
from datetime import date, datetime
import re

class TicketswapSpider(scrapy.Spider):
    name = 'ticketbeurs'
    start_urls = ['http://www.ticketbeurs.nl/Kopen.aspx']

    def parse(self, response):
        table = response.xpath('//div[@id="ContentPlaceHolder1_FestivalsTable"]/div[@class="row"]')
        for row in table:
            if not row.xpath('.//h3/text()').get():
                stats = StatsItem()
                stats['beschikbaar'] = row.xpath('./div[@class="col-sm-4"]/span[@class="titlefont"]/text()').get()
                data = row.xpath('./div[@class="col-sm-4"]/div[@class="hidden-xs"]/span/text()').getall()
                stats['verkocht'] = re.sub('[^0-9]', '', data[0])
                stats['gezocht'] = re.sub('[^0-9]', '', data[0])
                url = 'http://www.ticketbeurs.nl/' + row.xpath('./div/a/@href').get().strip()
                yield scrapy.Request(url, callback=self.parse_ticket, 
                                    meta={'stats': stats})

    def parse_ticket(self, response):
        item = EventItem()
        item['name'] = response.xpath('//center/h1/text()').get()
        item['event_href'] = response.url.split('=')[1]
        item['ticket_href'] = item['event_href']
        item['event_date'] = response.xpath('//center[h1]/h5/text()')[0].get().strip()
        data = response.xpath('//center[h1]/h5/text()').getall()[1].split(',')
        if len(data) >= 2: 
            item['city'] = data[0].strip() 
            item['location'] = data[1].strip()
        else:
            item['city'] = data[0].strip()
        yield item

        stats = response.meta['stats']
        stats['event_href'] = item['event_href']
        stats['ticket_href'] = item['event_href']
        stats['platform'] = 'TB'
        stats['time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        yield stats
