# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FilmItem(scrapy.Item):
    titre = scrapy.Field()
    annee = scrapy.Field()
    realisateur = scrapy.Field()
    note_presse = scrapy.Field()
    note_spectateurs = scrapy.Field()
    url = scrapy.Field()
