# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EventItem(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    event_href = scrapy.Field()
    ticket_href = scrapy.Field()
    event_date = scrapy.Field()
    location = scrapy.Field()
    city = scrapy.Field()
    country = scrapy.Field()
    platform = scrapy.Field()

class StatsItem(scrapy.Item):
    event_href = scrapy.Field()
    ticket_href = scrapy.Field()
    beschikbaar = scrapy.Field()
    verkocht = scrapy.Field()
    gezocht = scrapy.Field()
    time = scrapy.Field()
    platform = scrapy.Field()