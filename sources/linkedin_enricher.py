import html
import re

from datetime import datetime

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),

    "Accept-Language":
        "fr-FR,fr;q=0.9,en;q=0.8",
}


DESCRIPTION_SELECTORS = [
    "div.show-more-less-html__markup",
    "div.description__text",
    "section.description",
    "div.jobs-description-content__text",
    "div.jobs-box__html-content",
    "div.jobs-description__content",
]


MIN_DESCRIPTION_LENGTH = 300


# ============================================================
# NETTOYAGE TEXTE
# ============================================================

def nettoyer_texte(
    texte
):

    if not texte:
        return ""

    texte = html.unescape(
        str(
            texte
        )
    )

    texte = (
        texte
        .replace(
            "\xa0",
            " "
        )
        .replace(
            "\u202f",
            " "
        )
        .replace(
            "\u200b",
            ""
        )
    )

    lignes = []

    for ligne in texte.splitlines():

        ligne = re.sub(
            r"[ \t]+",
            " ",
            ligne
        ).strip()

        if ligne:

            lignes.append(
                ligne
            )

    return "\n".join(
        lignes
    ).strip()


def texte_element(
    element
):

    if element is None:
        return ""

    return nettoyer_texte(
        element.get_text(
            "\n",
            strip=True
        )
    )


# ============================================================
# NETTOYAGE SPECIFIQUE LINKEDIN
# ============================================================

def nettoyer_description_linkedin(
    texte
):

    texte = nettoyer_texte(
        texte
    )

    if not texte:
        return ""

    lignes = texte.splitlines()

    lignes_nettoyees = []

    ignorer_prefixes = [
        "Envoyer un message directement",
        "Voir qui ",
        "Découvrez qui ",
        "Découvrez les relations",
        "Identifiez-vous pour",
        "S’identifier pour",
        "S'identifier pour",
    ]

    for ligne in lignes:

        ligne = ligne.strip()

        if not ligne:
            continue

        if any(
            ligne.casefold().startswith(
                prefixe.casefold()
            )
            for prefixe in ignorer_prefixes
        ):

            continue

        lignes_nettoyees.append(
            ligne
        )

    return "\n".join(
        lignes_nettoyees
    ).strip()


# ============================================================
# DESCRIPTION
# ============================================================

def extraire_description(
    soup
):

    candidats = []

    # --------------------------------------------------------
    # SELECTEURS CONNUS
    # --------------------------------------------------------

    for selecteur in DESCRIPTION_SELECTORS:

        for element in soup.select(
            selecteur
        ):

            texte = nettoyer_description_linkedin(
                texte_element(
                    element
                )
            )

            longueur = len(
                texte
            )

            if longueur < MIN_DESCRIPTION_LENGTH:
                continue

            if longueur > 30000:
                continue

            candidats.append(
                {
                    "texte":
                        texte,

                    "longueur":
                        longueur,

                    "methode":
                        selecteur,
                }
            )

    if candidats:

        candidats.sort(
            key=lambda x:
                x[
                    "longueur"
                ],
            reverse=True,
        )

        return candidats[
            0
        ]

    # --------------------------------------------------------
    # FALLBACK : CLASSES CONTENANT "description"
    # --------------------------------------------------------

    for element in soup.find_all(
        class_=re.compile(
            r"description",
            re.IGNORECASE,
        )
    ):

        texte = nettoyer_description_linkedin(
            texte_element(
                element
            )
        )

        longueur = len(
            texte
        )

        if longueur < MIN_DESCRIPTION_LENGTH:
            continue

        if longueur > 30000:
            continue

        candidats.append(
            {
                "texte":
                    texte,

                "longueur":
                    longueur,

                "methode":
                    "class_description",
            }
        )

    if not candidats:
        return None

    candidats.sort(
        key=lambda x:
            x[
                "longueur"
            ],
        reverse=True,
    )

    return candidats[
        0
    ]


# ============================================================
# METADONNEES
# ============================================================

def extraire_titre(
    soup
):

    selecteurs = [
        "h1.top-card-layout__title",
        "h1",
    ]

    for selecteur in selecteurs:

        texte = texte_element(
            soup.select_one(
                selecteur
            )
        )

        if texte:
            return texte

    return ""


def extraire_entreprise(
    soup
):

    selecteurs = [
        "a.topcard__org-name-link",
        "span.topcard__flavor",
    ]

    for selecteur in selecteurs:

        texte = texte_element(
            soup.select_one(
                selecteur
            )
        )

        if texte:
            return texte

    return ""


def extraire_lieu(
    soup
):

    selecteurs = [
        "span.topcard__flavor--bullet",
        "span.top-card-layout__first-subline",
    ]

    for selecteur in selecteurs:

        texte = texte_element(
            soup.select_one(
                selecteur
            )
        )

        if texte:
            return texte

    return ""


# ============================================================
# TELECHARGEMENT D'UNE PAGE LINKEDIN
# ============================================================

def enrichir_url(
    url,
    timeout=25,
):

    resultat = {
        "ok":
            False,

        "status":
            None,

        "url_finale":
            "",

        "titre":
            "",

        "entreprise":
            "",

        "lieu":
            "",

        "description":
            "",

        "description_longueur":
            0,

        "methode":
            "",

        "erreur":
            "",
    }

    if not url:

        resultat[
            "erreur"
        ] = "URL vide"

        return resultat

    try:

        reponse = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )

        resultat[
            "status"
        ] = reponse.status_code

        resultat[
            "url_finale"
        ] = reponse.url

        if reponse.status_code != 200:

            resultat[
                "erreur"
            ] = (
                f"HTTP {reponse.status_code}"
            )

            return resultat

        soup = BeautifulSoup(
            reponse.text,
            "html.parser"
        )

        resultat[
            "titre"
        ] = extraire_titre(
            soup
        )

        resultat[
            "entreprise"
        ] = extraire_entreprise(
            soup
        )

        resultat[
            "lieu"
        ] = extraire_lieu(
            soup
        )

        description = extraire_description(
            soup
        )

        if not description:

            resultat[
                "erreur"
            ] = (
                "Description complète non trouvée"
            )

            return resultat

        resultat[
            "description"
        ] = description[
            "texte"
        ]

        resultat[
            "description_longueur"
        ] = description[
            "longueur"
        ]

        resultat[
            "methode"
        ] = description[
            "methode"
        ]

        resultat[
            "ok"
        ] = (
            resultat[
                "description_longueur"
            ]
            >= MIN_DESCRIPTION_LENGTH
        )

        if not resultat[
            "ok"
        ]:

            resultat[
                "erreur"
            ] = (
                "Description trop courte"
            )

        return resultat

    except Exception as erreur:

        resultat[
            "erreur"
        ] = str(
            erreur
        )

        return resultat


# ============================================================
# ENRICHISSEMENT D'UNE OFFRE LINKEDIN
# ============================================================

def enrichir_offre_linkedin(
    offre
):

    if not isinstance(
        offre,
        dict
    ):

        return offre

    if offre.get(
        "source"
    ) != "LinkedIn":

        return offre

    url = str(
        offre.get(
            "url",
            ""
        )
        or ""
    ).strip()

    if not url:

        return offre

    resultat = enrichir_url(
        url
    )

    donnees = offre.get(
        "donnees_brutes",
        {}
    )

    if not isinstance(
        donnees,
        dict
    ):

        donnees = {
            "contenu":
                str(
                    donnees
                )
        }

    # --------------------------------------------------------
    # ECHEC D'ENRICHISSEMENT
    # --------------------------------------------------------

    if not resultat[
        "ok"
    ]:

        donnees[
            "linkedin_enrichi"
        ] = False

        donnees[
            "linkedin_enrichissement_erreur"
        ] = resultat[
            "erreur"
        ]

        donnees[
            "linkedin_http_status"
        ] = resultat[
            "status"
        ]

        donnees[
            "linkedin_enrichissement_date"
        ] = datetime.now().isoformat(
            timespec="seconds"
        )

        offre[
            "donnees_brutes"
        ] = donnees

        return offre

    # --------------------------------------------------------
    # SUCCES
    # --------------------------------------------------------

    titre_extrait = str(
        resultat.get(
            "titre",
            ""
        )
        or ""
    ).strip()

    entreprise_extraite = str(
        resultat.get(
            "entreprise",
            ""
        )
        or ""
    ).strip()

    lieu_extrait = str(
        resultat.get(
            "lieu",
            ""
        )
        or ""
    ).strip()

    description = str(
        resultat.get(
            "description",
            ""
        )
        or ""
    ).strip()

    # Les métadonnées de la page prennent le dessus
    # uniquement lorsqu'elles existent.
    if titre_extrait:

        offre[
            "titre"
        ] = titre_extrait

    if entreprise_extraite:

        offre[
            "entreprise"
        ] = entreprise_extraite

    if lieu_extrait:

        offre[
            "lieu"
        ] = lieu_extrait

    offre[
        "description"
    ] = description

    if resultat.get(
        "url_finale"
    ):

        offre[
            "url"
        ] = resultat[
            "url_finale"
        ]

    donnees[
        "linkedin_enrichi"
    ] = True

    donnees[
        "linkedin_enrichissement_date"
    ] = datetime.now().isoformat(
        timespec="seconds"
    )

    donnees[
        "linkedin_description_longueur"
    ] = resultat[
        "description_longueur"
    ]

    donnees[
        "linkedin_methode_description"
    ] = resultat[
        "methode"
    ]

    donnees[
        "linkedin_http_status"
    ] = resultat[
        "status"
    ]

    donnees[
        "linkedin_url_finale"
    ] = resultat[
        "url_finale"
    ]

    offre[
        "donnees_brutes"
    ] = donnees

    return offre


# ============================================================
# VERIFICATION DE QUALITE
# ============================================================

def linkedin_description_complete(
    offre
):

    if not isinstance(
        offre,
        dict
    ):

        return False

    if offre.get(
        "source"
    ) != "LinkedIn":

        return True

    description = str(
        offre.get(
            "description",
            ""
        )
        or ""
    ).strip()

    if len(
        description
    ) < MIN_DESCRIPTION_LENGTH:

        return False

    donnees = offre.get(
        "donnees_brutes",
        {}
    )

    if not isinstance(
        donnees,
        dict
    ):

        return False

    return bool(
        donnees.get(
            "linkedin_enrichi"
        )
    )