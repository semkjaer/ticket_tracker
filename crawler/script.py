import os

items = ['events', 'stats']
for item in items:
    if os.path.exists(f'previous_{type}.csv'):
        os.remove(f'previous_{type}.csv')
    if os.path.exists(f'{type}.csv'):
        os.rename(f'{type}.csv', f'previous_{type}.csv')

spiders = os.popen('scrapy list').read()
for spider in spiders.split('\n'):
    if spider:
        os.system(f'scrapy crawl {spider}')

