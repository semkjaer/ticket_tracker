# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import EventItem, StatsItem
import logging
import pymongo
import csv

class CrawlerPipeline:

    def CSVWriter(self, item, file):
        fields = [x for x in item.keys()]
        with open(file,'a+') as f:
            f.write("{}\n".format(','.join(str(item[field]) for field in fields)))


    def process_item(self, item, spider):
        if isinstance(item, EventItem):
            self.CSVWriter(item, 'events.csv')
            return item

        elif isinstance(item, StatsItem):
            self.CSVWriter(item, 'stats.csv')
            return item
