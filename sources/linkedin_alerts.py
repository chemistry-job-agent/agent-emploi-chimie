import re

from html import unescape
from urllib.parse import unquote

from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

LINKEDIN_JOB_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?linkedin\.com/"
    r"(?:comm/)?jobs/view/"
    r"([^?\"'<>\s#]+)",
    re.IGNORECASE,
)

LINKEDIN_ID_PATTERN = re.compile(
    r"\d{6,}"
)

MODES_TRAVAIL = [
    "Sur site",
    "À distance",
    "A distance",
    "Hybride",
    "Remote",
    "Hybrid",
    "On-site",
    "On site",
]

TEXTES_GENERIQUES = {
    "",
    "linkedin",
    "voir l'offre",
    "voir l’offre",
    "voir le poste",
    "voir l'emploi",
    "voir l’emploi",
    "postuler",
    "candidature simplifiée",
    "easy apply",
    "en savoir plus",
}


# ============================================================
# NETTOYAGE
# ============================================================

def nettoyer_texte(texte):

    if not texte:
        return ""

    texte = unescape(
        str(texte)
    )

    texte = (
        texte
        .replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\u202f", " ")
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


# ============================================================
# URL / IDENTIFIANT LINKEDIN
# ============================================================

def extraire_id_linkedin(url):

    if not url:
        return ""

    url = unquote(
        unescape(
            str(url)
        )
    )

    match = LINKEDIN_JOB_URL_PATTERN.search(
        url
    )

    if not match:
        return ""

    partie_offre = match.group(
        1
    )

    identifiants = LINKEDIN_ID_PATTERN.findall(
        partie_offre
    )

    if not identifiants:
        return ""

    return identifiants[
        -1
    ]


def canonicaliser_url_linkedin(url):

    source_id = extraire_id_linkedin(
        url
    )

    if not source_id:
        return ""

    return (
        "https://www.linkedin.com/jobs/view/"
        f"{source_id}/"
    )


def extraire_urls_linkedin(contenu):

    if not contenu:
        return []

    contenu = unescape(
        str(contenu)
    )

    resultat = []

    for match in LINKEDIN_JOB_URL_PATTERN.finditer(
        contenu
    ):

        url_complete = match.group(
            0
        )

        url_propre = canonicaliser_url_linkedin(
            url_complete
        )

        if (
            url_propre
            and url_propre not in resultat
        ):

            resultat.append(
                url_propre
            )

    return resultat


# ============================================================
# MODE DE TRAVAIL
# ============================================================

def extraire_mode_travail(texte):

    texte = nettoyer_texte(
        texte
    )

    for mode in MODES_TRAVAIL:

        motif = re.compile(
            r"\(\s*"
            + re.escape(
                mode
            )
            + r"\s*\)",
            re.IGNORECASE,
        )

        if motif.search(
            texte
        ):

            if mode == "A distance":
                return "À distance"

            return mode

    return ""


# ============================================================
# SALAIRE
# ============================================================

def extraire_salaire(texte):

    texte = nettoyer_texte(
        texte
    )

    motifs = [
        (
            r"\bEntre\s+"
            r"\d[\d\s.,]*\s*k?\s*€"
            r"\s+et\s+"
            r"\d[\d\s.,]*\s*k?\s*€"
            r"(?:\s+par\s+(?:an|mois|heure))?"
        ),

        (
            r"\bÀ partir de\s+"
            r"\d[\d\s.,]*\s*k?\s*€"
            r"(?:\s+par\s+(?:an|mois|heure))?"
        ),

        (
            r"\bA partir de\s+"
            r"\d[\d\s.,]*\s*k?\s*€"
            r"(?:\s+par\s+(?:an|mois|heure))?"
        ),

        (
            r"\b\d[\d\s.,]*\s*k?\s*€"
            r"\s*[-–]\s*"
            r"\d[\d\s.,]*\s*k?\s*€"
            r"(?:\s+par\s+(?:an|mois|heure))?"
        ),
    ]

    for motif in motifs:

        match = re.search(
            motif,
            texte,
            flags=re.IGNORECASE,
        )

        if match:

            return nettoyer_texte(
                match.group(
                    0
                )
            )

    return ""


# ============================================================
# NETTOYAGE DU LIEU
# ============================================================

def nettoyer_lieu(texte):

    texte = nettoyer_texte(
        texte
    )

    if not texte:
        return ""

    for mode in MODES_TRAVAIL:

        texte = re.sub(
            r"\(\s*"
            + re.escape(
                mode
            )
            + r"\s*\)",
            " ",
            texte,
            flags=re.IGNORECASE,
        )

    expressions_a_retirer = [
        r"\bCandidature simplifiée\b",
        r"\bEasy Apply\b",
        r"\bPromu\b",
        r"\bPromoted\b",
        r"\bPostuler\b",
    ]

    for motif in expressions_a_retirer:

        texte = re.sub(
            motif,
            " ",
            texte,
            flags=re.IGNORECASE,
        )

    # Retire une éventuelle partie salaire.
    salaire = extraire_salaire(
        texte
    )

    if salaire:

        position = (
            texte.casefold()
            .find(
                salaire.casefold()
            )
        )

        if position >= 0:

            texte = texte[
                :position
            ]

    return nettoyer_texte(
        texte
    )


# ============================================================
# ENTREPRISE + LIEU
# ============================================================

def decomposer_entreprise_lieu(
    texte
):

    texte = nettoyer_texte(
        texte
    )

    if not texte:
        return "", "", ""

    if "·" not in texte:

        return "", "", ""

    entreprise, lieu_brut = (
        texte.split(
            "·",
            1
        )
    )

    entreprise = nettoyer_texte(
        entreprise
    )

    lieu_brut = nettoyer_texte(
        lieu_brut
    )

    mode = extraire_mode_travail(
        lieu_brut
    )

    lieu = nettoyer_lieu(
        lieu_brut
    )

    return (
        entreprise,
        lieu,
        mode,
    )


# ============================================================
# CREATION NORMALISEE DE L'OFFRE
# ============================================================

def creer_offre_linkedin(
    url,
    titre="",
    entreprise="",
    lieu="",
    description="",
    contrat="",
    mode_travail="",
    salaire="",
    donnees_brutes=None,
):

    source_id = extraire_id_linkedin(
        url
    )

    if donnees_brutes is None:

        donnees_brutes = {}

    donnees = {
        "origine":
            "alerte_linkedin",

        "mode_travail":
            nettoyer_texte(
                mode_travail
            ),
    }

    donnees.update(
        donnees_brutes
    )

    return {
        "source":
            "LinkedIn",

        "source_id":
            source_id,

        "titre":
            nettoyer_texte(
                titre
            ),

        "entreprise":
            nettoyer_texte(
                entreprise
            ),

        "lieu":
            nettoyer_lieu(
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
            canonicaliser_url_linkedin(
                url
            ),

        "date_publication":
            "",

        "experience":
            "",

        "salaire":
            nettoyer_texte(
                salaire
            ),

        "donnees_brutes":
            donnees,
    }


# ============================================================
# VALIDATION D'UN TITRE
# ============================================================

def titre_est_valide(texte):

    texte = nettoyer_texte(
        texte
    )

    if not texte:
        return False

    if (
        texte.casefold()
        in {
            valeur.casefold()
            for valeur in TEXTES_GENERIQUES
        }
    ):

        return False

    if texte.isdigit():
        return False

    return len(
        texte
    ) >= 4


# ============================================================
# DECOMPOSITION D'UNE ANCRE LINKEDIN
# ============================================================

def analyser_ancre_linkedin(
    ancre
):

    href = ancre.get(
        "href",
        ""
    )

    source_id = extraire_id_linkedin(
        href
    )

    if not source_id:

        return None

    morceaux = [
        nettoyer_texte(
            morceau
        )
        for morceau in ancre.stripped_strings
    ]

    morceaux = [
        morceau
        for morceau in morceaux
        if morceau
    ]

    if not morceaux:

        return {
            "source_id":
                source_id,

            "url":
                canonicaliser_url_linkedin(
                    href
                ),

            "titre":
                "",

            "entreprise":
                "",

            "lieu":
                "",

            "mode":
                "",

            "salaire":
                "",

            "badge":
                "",

            "morceaux":
                [],
        }

    titre = nettoyer_texte(
        morceaux[
            0
        ]
    )

    entreprise = ""
    lieu = ""
    mode = ""
    salaire = ""
    badge = ""

    # LinkedIn structure normalement la carte ainsi :
    #
    # 1. Titre
    # 2. Entreprise · Lieu (mode)
    # 3. Badge / salaire / information complémentaire
    #
    # On cherche néanmoins le morceau avec "·"
    # au lieu de supposer qu'il est toujours en position 2.

    index_meta = None

    for index, morceau in enumerate(
        morceaux[
            1:
        ],
        start=1,
    ):

        if "·" in morceau:

            index_meta = index
            break

    if index_meta is not None:

        entreprise, lieu, mode = (
            decomposer_entreprise_lieu(
                morceaux[
                    index_meta
                ]
            )
        )

    # Cherche le salaire dans tous les morceaux.
    for morceau in morceaux:

        salaire_trouve = extraire_salaire(
            morceau
        )

        if salaire_trouve:

            salaire = salaire_trouve
            break

    # Les autres morceaux peuvent être des badges.
    autres = []

    for index, morceau in enumerate(
        morceaux[
            1:
        ],
        start=1,
    ):

        if index == index_meta:
            continue

        # Ne répète pas une information salaire.
        if (
            salaire
            and salaire.casefold()
            in morceau.casefold()
        ):
            continue

        autres.append(
            morceau
        )

    if autres:

        badge = " | ".join(
            autres
        )

    return {
        "source_id":
            source_id,

        "url":
            canonicaliser_url_linkedin(
                href
            ),

        "titre":
            titre,

        "entreprise":
            entreprise,

        "lieu":
            lieu,

        "mode":
            mode,

        "salaire":
            salaire,

        "badge":
            badge,

        "morceaux":
            morceaux,
    }


# ============================================================
# SCORE DE QUALITE D'UNE ANCRE
# ============================================================

def score_ancre(
    donnees
):

    if not donnees:
        return -1

    score = 0

    titre = donnees.get(
        "titre",
        ""
    )

    entreprise = donnees.get(
        "entreprise",
        ""
    )

    lieu = donnees.get(
        "lieu",
        ""
    )

    morceaux = donnees.get(
        "morceaux",
        []
    )

    if titre_est_valide(
        titre
    ):

        score += 100

    if entreprise:

        score += 100

    if lieu:

        score += 100

    if len(
        morceaux
    ) >= 2:

        score += 20

    if len(
        morceaux
    ) >= 3:

        score += 5

    return score


# ============================================================
# EXTRACTION HTML LINKEDIN
# ============================================================

def extraire_offres_linkedin_html(
    html
):

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    meilleurs = {}

    for ancre in soup.find_all(
        "a",
        href=True,
    ):

        donnees = analyser_ancre_linkedin(
            ancre
        )

        if not donnees:
            continue

        source_id = donnees[
            "source_id"
        ]

        nouveau_score = score_ancre(
            donnees
        )

        ancien = meilleurs.get(
            source_id
        )

        if ancien is None:

            meilleurs[
                source_id
            ] = donnees

            continue

        ancien_score = score_ancre(
            ancien
        )

        if nouveau_score > ancien_score:

            meilleurs[
                source_id
            ] = donnees

    offres = []

    for source_id, donnees in (
        meilleurs.items()
    ):

        titre = donnees.get(
            "titre",
            ""
        )

        if not titre_est_valide(
            titre
        ):

            titre = (
                f"Offre LinkedIn "
                f"{source_id}"
            )

        morceaux = donnees.get(
            "morceaux",
            []
        )

        description = " | ".join(
            morceaux
        )

        offre = creer_offre_linkedin(
            url=donnees.get(
                "url",
                ""
            ),

            titre=titre,

            entreprise=donnees.get(
                "entreprise",
                ""
            ),

            lieu=donnees.get(
                "lieu",
                ""
            ),

            description=description,

            mode_travail=donnees.get(
                "mode",
                ""
            ),

            salaire=donnees.get(
                "salaire",
                ""
            ),

            donnees_brutes={
                "morceaux_alerte":
                    morceaux,

                "badge":
                    donnees.get(
                        "badge",
                        ""
                    ),
            },
        )

        offres.append(
            offre
        )

    return offres


# ============================================================
# EXTRACTION TEXTE - FALLBACK
# ============================================================

def extraire_offres_linkedin_texte(
    texte
):

    if not texte:
        return []

    lignes = [
        nettoyer_texte(
            ligne
        )
        for ligne in str(
            texte
        ).splitlines()
    ]

    lignes = [
        ligne
        for ligne in lignes
        if ligne
    ]

    offres = []
    vus = set()

    for index, ligne in enumerate(
        lignes
    ):

        source_id = extraire_id_linkedin(
            ligne
        )

        if not source_id:
            continue

        if source_id in vus:
            continue

        vus.add(
            source_id
        )

        contexte = lignes[
            max(
                0,
                index - 6
            ):
            index
        ]

        titre = ""

        # Sans structure HTML, on reste volontairement
        # conservateur : aucune entreprise ou lieu n'est
        # inventé par découpage approximatif.
        for candidat in reversed(
            contexte
        ):

            if (
                titre_est_valide(
                    candidat
                )
                and "linkedin.com"
                not in candidat.casefold()
            ):

                titre = candidat
                break

        if not titre:

            titre = (
                f"Offre LinkedIn "
                f"{source_id}"
            )

        url = (
            "https://www.linkedin.com/jobs/view/"
            f"{source_id}/"
        )

        offre = creer_offre_linkedin(
            url=url,
            titre=titre,
            description=" | ".join(
                contexte
            ),
            donnees_brutes={
                "mode_extraction":
                    "texte_fallback"
            },
        )

        offres.append(
            offre
        )

    return offres