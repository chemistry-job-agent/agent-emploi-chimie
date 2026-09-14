import re
from html import unescape
from urllib.parse import (
    urlparse,
    parse_qs
)


INDEED_URL_PATTERN = re.compile(
    r'https?://(?:[a-z]{2}\.)?(?:www\.)?indeed\.[a-z.]+/'
    r'[^"\'<>\s]+',
    re.IGNORECASE
)


def nettoyer_texte(texte):

    if not texte:
        return ""

    texte = unescape(
        str(texte)
    )

    texte = re.sub(
        r"<[^>]+>",
        " ",
        texte
    )

    texte = re.sub(
        r"\s+",
        " ",
        texte
    )

    return texte.strip()


def extraire_urls_indeed(contenu):

    if not contenu:
        return []

    urls = INDEED_URL_PATTERN.findall(
        contenu
    )

    urls_uniques = []

    for url in urls:

        url = unescape(
            url
        )

        if url not in urls_uniques:
            urls_uniques.append(
                url
            )

    return urls_uniques


def extraire_id_indeed(url):

    if not url:
        return ""

    donnees_url = urlparse(
        url
    )

    parametres = parse_qs(
        donnees_url.query
    )

    # Identifiant principal Indeed
    for cle in (
        "jk",
        "vjk"
    ):

        valeurs = parametres.get(
            cle
        )

        if valeurs:
            return valeurs[0]

    return ""


def creer_offre_indeed(
    url,
    titre="",
    entreprise="",
    lieu="",
    description="",
    contrat=""
):

    return {
        "source":
            "Indeed",

        "source_id":
            extraire_id_indeed(
                url
            ),

        "titre":
            nettoyer_texte(
                titre
            ),

        "entreprise":
            nettoyer_texte(
                entreprise
            ),

        "lieu":
            nettoyer_texte(
                lieu
            ),

        "contrat":
            nettoyer_texte(
                contrat
            ),

        "description":
            nettoyer_texte(
                description
            ),

        "url":
            url,

        "date_publication":
            "",

        "experience":
            "",

        "salaire":
            "",

        "donnees_brutes": {
            "origine":
                "alerte_indeed"
        }
    }