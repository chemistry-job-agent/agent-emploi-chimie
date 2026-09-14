import re
from html import unescape


APEC_DETAIL_PATTERN = re.compile(
    r'https?://(?:www\.)?apec\.fr/'
    r'candidat/recherche-emploi\.html/'
    r'emploi/detail-offre/[^"\'<>\s]+',
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


def extraire_urls_apec(contenu):

    if not contenu:
        return []

    urls = APEC_DETAIL_PATTERN.findall(
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


def extraire_id_apec(url):

    if not url:
        return ""

    match = re.search(
        r"/detail-offre/([^/?#]+)",
        url
    )

    if not match:
        return ""

    return match.group(1)


def creer_offre_apec_depuis_email(
    url,
    titre="",
    entreprise="",
    lieu="",
    description=""
):

    return {
        "source":
            "Apec",

        "source_id":
            extraire_id_apec(
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
            "",

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
                "alerte_email_apec"
        }
    }