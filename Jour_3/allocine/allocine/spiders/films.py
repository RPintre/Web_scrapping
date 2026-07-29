import re

import scrapy

from allocine.items import FilmItem

# Top 200 films = 20 pages de 10 films sur allocine.fr/film/meilleurs/
NB_PAGES = 20


class FilmsSpider(scrapy.Spider):
    name = "films"
    allowed_domains = ["allocine.fr"]
    start_urls = ["https://www.allocine.fr/film/meilleurs/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
    }

    def parse(self, response):
        for lien in response.css("h2.meta-title a::attr(href)").getall():
            yield response.follow(lien, callback=self.parse_film)

        # Le sujet propose "a.button--right" pour le lien "page suivante",
        # mais il n'existe plus (verifie dans scrapy shell) : la pagination
        # n'affiche que des numeros ?page=N. Du coup je reconstruis l'URL
        # suivante moi-meme jusqu'a la page 20 (= top 200 films).
        page_actuelle = int(response.url.split("page=")[-1]) if "page=" in response.url else 1
        if page_actuelle < NB_PAGES:
            page_suivante = f"https://www.allocine.fr/film/meilleurs/?page={page_actuelle + 1}"
            yield response.follow(page_suivante, callback=self.parse)

    def parse_film(self, response):
        # Le sujet propose h1::text, mais le h1 d'AlloCine colle "Titre de
        # Realisateur(s)", et le nombre de noms colles ne correspond pas
        # toujours a la liste complete des realisateurs (Spider-Man: New
        # Generation par exemple, 3 credites mais 2 seulement dans le h1).
        # og:title donne le titre tout seul, plus simple.
        titre = response.css('meta[property="og:title"]::attr(content)').get(default="").strip()

        # Une fiche peut avoir deux blocs .meta-body-direction (realisateur
        # "De" et scenariste "Par") : on ne garde que le premier.
        bloc_realisateur = response.css(".meta-body-direction")[:1]
        realisateurs = [r.strip() for r in bloc_realisateur.css("span.dark-grey-link::text").getall()]
        realisateur = ", ".join(realisateurs) if realisateurs else None

        date_sortie = response.css(".meta-body-info span.date::text").get(default="")
        annee_match = re.search(r"\b(19|20)\d{2}\b", date_sortie)

        yield FilmItem(
            titre=titre,
            annee=annee_match.group(0) if annee_match else None,
            realisateur=realisateur,
            note_presse=self._note(response, "Presse"),
            note_spectateurs=self._note(response, "Spectateurs"),
            url=response.url,
        )

    @staticmethod
    def _note(response, label):
        # ".stareval-note:last-child::text" (propose dans le sujet) suppose
        # que la note presse est toujours affichee avant celle du public.
        # Faux des qu'un film n'a pas de note presse (assez frequent), donc
        # on cible directement le bloc qui porte le bon libelle.
        note = response.xpath(
            f'//div[@class="rating-item"][.//span[contains(@class,"rating-title") '
            f'and contains(normalize-space(.),"{label}")]]'
            f'//span[contains(@class,"stareval-note")]/text()'
        ).get()
        return note.strip() if note else None
