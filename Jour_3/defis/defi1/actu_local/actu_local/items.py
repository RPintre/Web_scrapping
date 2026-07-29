# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArticleItem(scrapy.Item):
    titre = scrapy.Field()
    lien = scrapy.Field()
    publication = scrapy.Field()  # heure + lieu (ex: "11:00 - Nangis")
