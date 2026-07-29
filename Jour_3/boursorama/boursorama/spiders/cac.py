import scrapy

from boursorama.items import ActionItem


class CacSpider(scrapy.Spider):
    name = "cac"
    allowed_domains = ["boursorama.com"]
    start_urls = ["https://www.boursorama.com/bourse/actions/palmares/france/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
    }

    def parse(self, response):
        # Le sujet propose "table.c-table tr", mais c'est trop generique :
        # la page a plusieurs tableaux "c-table" (les indicateurs
        # hausse/baisse tout en haut, entre autres). Le vrai tableau du
        # palmares a sa propre classe, "c-table-top-flop" (verifie dans
        # scrapy shell).
        for ligne in response.css("table.c-table-top-flop tr.c-table__row"):
            lien = ligne.css("a.c-link::attr(href)").get()
            if not lien:
                continue  # ligne d'en-tete (th), pas une valeur

            libelle = ligne.css("a.c-link::text").get(default="").strip()
            cours_brut = ligne.css("span.c-instrument--last::text").get(default="0")
            variation_brut = ligne.css("span.c-instrument--instant-variation::text").get(default="0")
            volume_brut = ligne.css("span.c-instrument--totalvolume::text").get(default="0")

            try:
                cours = float(cours_brut.replace(",", ".").strip())
            except (ValueError, TypeError):
                cours = 0.0
            try:
                variation = float(variation_brut.replace(",", ".").replace("%", "").strip())
            except (ValueError, TypeError):
                variation = 0.0
            try:
                volume = int(volume_brut.replace(" ", "").replace("\xa0", "").strip() or 0)
            except (ValueError, TypeError):
                volume = 0

            # Le sujet suggere de lire l'ISIN dans l'URL de la fiche
            # (href.split("/")[-2]). En verifiant dans scrapy shell, ce
            # bout d'URL ("1rPSOP") est en fait le symbole interne de
            # Boursorama, pas un code ISIN. Le vrai ISIN n'apparait que sur
            # la fiche detail, dans "h2.c-faceplate__isin".
            yield response.follow(
                lien,
                callback=self.parse_action,
                cb_kwargs={
                    "libelle": libelle,
                    "cours": cours,
                    "variation": variation,
                    "volume": volume,
                },
            )

    def parse_action(self, response, libelle, cours, variation, volume):
        isin_brut = response.css(".c-faceplate__isin::text").get(default="")
        isin = isin_brut.strip().split(" ")[0] if isin_brut.strip() else None

        yield ActionItem(
            libelle=libelle,
            cours=cours,
            variation=variation,
            volume=volume,
            isin=isin,
        )
