import scrapy

from actu_local.items import ArticleItem


class ActuSpider(scrapy.Spider):
    """Defi 1 : site local, la une d'actu.fr (edition Ile-de-France)."""

    name = "actu"
    allowed_domains = ["actu.fr"]
    start_urls = ["https://actu.fr/ile-de-france/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
    }

    def parse(self, response):
        # Le site utilise 3 gabarits de carte selon leur position sur la
        # page (mosaique, liste, mise en avant), et le titre se retrouve
        # tantot dans un h1, tantot un h2, tantot un h3 a l'interieur du
        # lien. Avec un selecteur h1/h2 seul, 30 cartes sur 45 etaient
        # ignorees.
        for carte in response.css(".ac-preview-article"):
            yield ArticleItem(
                titre=carte.css("a h1::text, a h2::text, a h3::text").get(default=""),
                lien=carte.css("a::attr(href)").get(default=""),
                publication=carte.css(".ac-preview-article__footer::text").get(default=""),
            )
