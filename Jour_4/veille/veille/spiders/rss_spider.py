import scrapy

from veille.items import MentionItem

CIBLE = "SNCF"  # mot-cle a surveiller

MOTS_NEGATIFS = ["fraude", "amende", "condamne", "scandale", "plainte",
                  "liquidation", "faillite", "perquisition", "accuse"]
MOTS_POSITIFS = ["croissance", "benefice", "record", "acquisition", "innovation",
                  "nomination", "partenariat", "expansion", "investissement"]

FLUX_RSS = [
    # Le sujet propose les flux "une" generalistes (rss_une.xml,
    # figaro_actualites.xml, flux-toutes-les-actualites) : testes en
    # pratique, ils ne remontent quasiment jamais SNCF -- ce sont des
    # tickers d'actualite chaude qui tournent en quelques minutes, pas
    # des flux de fond. Les rubriques Economie des memes medias captent
    # beaucoup mieux une veille sur une entreprise/institution (verifie
    # en direct : 3 a 4 mentions SNCF au moment du crawl contre 0 sur les
    # flux generalistes). Les Echos garde le flux "une" du sujet a titre
    # de temoin : il 403 systematiquement (voir README).
    "https://www.lemonde.fr/economie/rss_full.xml",
    "https://www.lesechos.fr/rss/rss_une.xml",
    "https://www.lefigaro.fr/rss/figaro_economie.xml",
    "https://www.bfmtv.com/rss/economie/",
    "https://www.01net.com/feed/",
]


class RssSpider(scrapy.Spider):
    name = "rss_spider"
    start_urls = FLUX_RSS

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "USER_AGENT": "IPSSI-OSINT-veille (+r.pintre@gmail.com)",
        "LOG_LEVEL": "INFO",
    }

    def parse(self, response):
        # Parser flux RSS/Atom
        for item in response.xpath("//item | //entry"):
            titre = item.xpath("title/text()").get("").strip()
            resume = item.xpath("description/text() | summary/text()").get("").strip()[:300]

            # Filtrer uniquement les articles mentionnant la cible
            if CIBLE.lower() not in (titre + resume).lower():
                continue

            url = item.xpath("link/text() | link/@href").get("").strip()
            date_pub = item.xpath("pubDate/text() | published/text()").get("").strip()
            source = response.url.split("/")[2]

            # Calcul du score d'alerte
            texte = (titre + " " + resume).lower()
            neg = sum(1 for m in MOTS_NEGATIFS if m in texte)
            pos = sum(1 for m in MOTS_POSITIFS if m in texte)
            score = 1 if neg > pos else (2 if pos > neg else 0)

            yield MentionItem(
                titre=titre, url=url, source=source,
                date_publi=date_pub, resume=resume, score_alerte=score,
            )
