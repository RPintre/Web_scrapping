# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import re

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

# Certains liens de actu.fr sont mal formes par le site lui-meme :
# "https://actu.fr/https:/actu.fr/ile-de-france/..." (domaine duplique).
HREF_CASSE = re.compile(r"^https://actu\.fr/https:/")


class CleanPipeline:
    """Nettoie les textes et repare les liens casses par le site source."""

    def process_item(self, item, spider):
        a = ItemAdapter(item)

        for champ in ("titre", "publication"):
            if a.get(champ):
                a[champ] = " ".join(a[champ].split())

        if a.get("lien"):
            a["lien"] = HREF_CASSE.sub("https://", a["lien"])

        if not a.get("titre") or not a.get("lien"):
            raise DropItem(f"Titre ou lien manquant : {a.asdict()}")

        return item
