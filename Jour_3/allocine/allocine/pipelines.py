# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class CleanPipeline:
    """Nettoie et caste les donnees."""

    def process_item(self, item, spider):
        a = ItemAdapter(item)

        for field in ["titre", "realisateur"]:
            if a.get(field):
                a[field] = a[field].strip()

        if not a.get("titre"):
            raise DropItem(f"Titre manquant : {a.asdict()}")

        if a.get("annee"):
            try:
                a["annee"] = int(a["annee"])
            except (TypeError, ValueError):
                a["annee"] = None

        for field in ["note_presse", "note_spectateurs"]:
            try:
                raw = (a.get(field) or "").replace(",", ".")
                a[field] = float(raw)
            except (ValueError, TypeError):
                a[field] = None

        return item
