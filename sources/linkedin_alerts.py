import re
from html import unescape


LINKEDIN_JOB_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/'
    r'jobs/view/[^"\'<>\s]+',
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


def extraire_urls_linkedin(contenu):

    if not contenu:
        return []

    urls = LINKEDIN_JOB_PATTERN.findall(
        contenu
    )

    urls_uniques = []

    for url in urls:

        url = unescape(
            url
        )

        # Retire certains paramètres de suivi
        url = url.split("?")[0]

        if url not in urls_uniques:
            urls_uniques.append(
                url
            )

    return urls_uniques


def extraire_id_linkedin(url):

    if not url:
        return ""

    # LinkedIn termine généralement l'URL
    # par l'identifiant numérique de l'offre.
    nombres = re.findall(
        r"\d{6,}",
        url
    )

    if not nombres:
        return ""

    return nombres[-1]


def creer_offre_linkedin(
    url,
    titre="",
    entreprise="",
    lieu="",
    description="",
    contrat=""
):

    return {
        "source":
            "LinkedIn",

        "source_id":
            extraire_id_linkedin(
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
                "alerte_linkedin"
        }
    }