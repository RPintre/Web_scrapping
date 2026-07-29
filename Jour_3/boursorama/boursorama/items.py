# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ActionItem(scrapy.Item):
    libelle = scrapy.Field()
    cours = scrapy.Field()  # float
    variation = scrapy.Field()  # float (ex: -0.53 pour -0.53%)
    volume = scrapy.Field()  # int
    isin = scrapy.Field()  # cle UNIQUE en BDD
