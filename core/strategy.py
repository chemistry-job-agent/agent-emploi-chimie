import re
import unicodedata


# ============================================================
# PIPELINES
# ============================================================

PIPELINE_IDF = "IDF_PRIORITAIRE"
PIPELINE_AXE_PARIS = "AXE_PARIS"
PIPELINE_FRANCE = "FRANCE"
PIPELINE_EUROPE = "EUROPE_PREMIUM"
PIPELINE_ALGERIE = "ALGERIE"
PIPELINE_GOLFE = "GOLFE"
PIPELINE_INTERNATIONAL = "INTERNATIONAL"


# ============================================================
# NORMALISATION
# ============================================================

def normaliser(texte):
    texte = str(texte or "").lower().strip()

    texte = unicodedata.normalize(
        "NFKD",
        texte
    )

    texte = "".join(
        caractere
        for caractere in texte
        if not unicodedata.combining(caractere)
    )

    texte = re.sub(
        r"\s+",
        " ",
        texte
    )

    return texte


def contient(texte, expressions):
    texte = normaliser(texte)

    return any(
        normaliser(expression) in texte
        for expression in expressions
    )


# ============================================================
# ZONES FRANCE
# ============================================================

IDF = [
    "paris",
    "ile-de-france",
    "ile de france",

    "essonne",
    "evry",
    "evry-courcouronnes",
    "courcouronnes",
    "corbeil",
    "corbeil-essonnes",
    "grigny",
    "ris-orangis",
    "viry-chatillon",

    "massy",
    "palaiseau",
    "saclay",
    "orsay",
    "les ulis",

    "boulogne-billancourt",
    "nanterre",
    "courbevoie",
    "puteaux",
    "levallois",
    "issy-les-moulineaux",

    "creteil",
    "vitry-sur-seine",
    "villejuif",
    "rungis",

    "versailles",
    "saint-quentin-en-yvelines",

    "cergy",
    "argenteuil",

    "saint-denis",
    "aubervilliers",
    "montreuil",

    "marne-la-vallee",
    "noisy-le-grand",

    "75",
    "77",
    "78",
    "91",
    "92",
    "93",
    "94",
    "95"
]


AXE_ROUEN = [
    "rouen",
    "saint-etienne-du-rouvray",
    "le grand-quevilly",
    "le petit-quevilly",
    "val-de-reuil",
    "val de reuil",
    "evreux"
]


AXE_CENTRE = [
    "orleans",
    "chartres",
    "dreux"
]


HAUTS_DE_FRANCE = [
    "lille",
    "villeneuve-d'ascq",
    "villeneuve d'ascq",
    "arras",
    "amiens"
]


OCCITANIE_PRIORITAIRE = [
    "montpellier",
    "herault"
]


# ============================================================
# PAYS / INTERNATIONAL
# ============================================================

SUISSE = [
    "suisse",
    "switzerland",
    "geneve",
    "genève",
    "lausanne",
    "basel",
    "bale",
    "bâle",
    "zurich",
    "zürich",
    "fribourg",
    "neuchatel",
    "neuchâtel",
    "valais"
]


BELGIQUE = [
    "belgique",
    "belgium",
    "bruxelles",
    "brussels",
    "liege",
    "liège",
    "charleroi",
    "anvers",
    "antwerp",
    "gent",
    "ghent",
    "leuven",
    "louvain"
]


LUXEMBOURG = [
    "luxembourg"
]


ALGERIE = [
    "algerie",
    "algérie",
    "algeria",
    "alger",
    "oran",
    "constantine",
    "annaba",
    "blida",
    "setif",
    "sétif",
    "bejaia",
    "béjaïa",
    "tlemcen"
]


ARABIE_SAOUDITE = [
    "arabie saoudite",
    "saudi arabia",
    "riyadh",
    "djeddah",
    "jeddah",
    "dammam",
    "jubail"
]


EMIRATS = [
    "emirats arabes unis",
    "émirats arabes unis",
    "united arab emirates",
    "uae",
    "dubai",
    "abu dhabi",
    "sharjah"
]


QATAR = [
    "qatar",
    "doha"
]


OMAN = [
    "oman",
    "muscat"
]


ALLEMAGNE = [
    "allemagne",
    "germany",
    "deutschland",
    "berlin",
    "munich",
    "münchen",
    "frankfurt",
    "hamburg",
    "cologne",
    "köln",
    "dusseldorf",
    "düsseldorf",
    "leverkusen"
]


PAYS_BAS = [
    "pays-bas",
    "netherlands",
    "holland",
    "amsterdam",
    "rotterdam",
    "eindhoven",
    "utrecht",
    "maastricht"
]


IRLANDE = [
    "irlande",
    "ireland",
    "dublin",
    "cork",
    "galway",
    "limerick"
]


CANADA = [
    "canada",
    "quebec",
    "québec",
    "montreal",
    "montréal",
    "toronto",
    "ottawa",
    "vancouver",
    "calgary"
]


SENEGAL = [
    "senegal",
    "sénégal",
    "dakar"
]


SINGAPOUR = [
    "singapour",
    "singapore"
]


ROYAUME_UNI = [
    "royaume-uni",
    "united kingdom",
    "uk",
    "england",
    "scotland",
    "london",
    "cambridge",
    "oxford",
    "manchester"
]


DANEMARK = [
    "danemark",
    "denmark",
    "copenhagen",
    "copenhague"
]


SUEDE = [
    "suede",
    "suède",
    "sweden",
    "stockholm",
    "gothenburg",
    "goteborg",
    "göteborg"
]


AUTRICHE = [
    "autriche",
    "austria",
    "vienna",
    "vienne"
]


# ============================================================
# DETECTION
# ============================================================

def detecter_zone(lieu="", description=""):
    texte = f"{lieu} {description}"

    # --------------------------------------------------------
    # FRANCE - priorité personnelle
    # --------------------------------------------------------

    if contient(texte, IDF):
        return {
            "pays": "FRANCE",
            "zone": "ILE_DE_FRANCE",
            "pipeline": PIPELINE_IDF,
            "score_geographique": 100,
            "score_opportunite": 95
        }

    if contient(texte, AXE_ROUEN):
        return {
            "pays": "FRANCE",
            "zone": "ROUEN_NORMANDIE",
            "pipeline": PIPELINE_AXE_PARIS,
            "score_geographique": 90,
            "score_opportunite": 85
        }

    if contient(texte, AXE_CENTRE):
        return {
            "pays": "FRANCE",
            "zone": "ORLEANS_CHARTRES_DREUX",
            "pipeline": PIPELINE_AXE_PARIS,
            "score_geographique": 85,
            "score_opportunite": 82
        }

    if contient(texte, HAUTS_DE_FRANCE):
        return {
            "pays": "FRANCE",
            "zone": "HAUTS_DE_FRANCE",
            "pipeline": PIPELINE_FRANCE,
            "score_geographique": 75,
            "score_opportunite": 78
        }

    if contient(texte, OCCITANIE_PRIORITAIRE):
        return {
            "pays": "FRANCE",
            "zone": "MONTPELLIER_OCCITANIE",
            "pipeline": PIPELINE_FRANCE,
            "score_geographique": 78,
            "score_opportunite": 78
        }

    # --------------------------------------------------------
    # EUROPE À FORTE VALEUR
    # --------------------------------------------------------

    if contient(texte, SUISSE):
        return {
            "pays": "SUISSE",
            "zone": "SUISSE",
            "pipeline": PIPELINE_EUROPE,
            "score_geographique": 65,
            "score_opportunite": 100
        }

    if contient(texte, BELGIQUE):
        return {
            "pays": "BELGIQUE",
            "zone": "BELGIQUE",
            "pipeline": PIPELINE_EUROPE,
            "score_geographique": 70,
            "score_opportunite": 90
        }

    if contient(texte, LUXEMBOURG):
        return {
            "pays": "LUXEMBOURG",
            "zone": "LUXEMBOURG",
            "pipeline": PIPELINE_EUROPE,
            "score_geographique": 65,
            "score_opportunite": 88
        }

    if contient(texte, ALLEMAGNE):
        return {
            "pays": "ALLEMAGNE",
            "zone": "ALLEMAGNE",
            "pipeline": PIPELINE_EUROPE,
            "score_geographique": 55,
            "score_opportunite": 88
        }

    if contient(texte, PAYS_BAS):
        return {
            "pays": "PAYS_BAS",
            "zone": "PAYS_BAS",
            "pipeline": PIPELINE_EUROPE,
            "score_geographique": 55,
            "score_opportunite": 86
        }

    if contient(texte, IRLANDE):
        return {
            "pays": "IRLANDE",
            "zone": "IRLANDE",
            "pipeline": PIPELINE_EUROPE,
            "score_geographique": 50,
            "score_opportunite": 88
        }

    # --------------------------------------------------------
    # ALGERIE
    # --------------------------------------------------------

    if contient(texte, ALGERIE):
        return {
            "pays": "ALGERIE",
            "zone": "ALGERIE",
            "pipeline": PIPELINE_ALGERIE,
            "score_geographique": 75,
            "score_opportunite": 85
        }

    # --------------------------------------------------------
    # GOLFE
    # --------------------------------------------------------

    if contient(texte, ARABIE_SAOUDITE):
        return {
            "pays": "ARABIE_SAOUDITE",
            "zone": "GOLFE",
            "pipeline": PIPELINE_GOLFE,
            "score_geographique": 45,
            "score_opportunite": 90
        }

    if contient(texte, EMIRATS):
        return {
            "pays": "EMIRATS_ARABES_UNIS",
            "zone": "GOLFE",
            "pipeline": PIPELINE_GOLFE,
            "score_geographique": 45,
            "score_opportunite": 90
        }

    if contient(texte, QATAR):
        return {
            "pays": "QATAR",
            "zone": "GOLFE",
            "pipeline": PIPELINE_GOLFE,
            "score_geographique": 40,
            "score_opportunite": 82
        }

    if contient(texte, OMAN):
        return {
            "pays": "OMAN",
            "zone": "GOLFE",
            "pipeline": PIPELINE_GOLFE,
            "score_geographique": 40,
            "score_opportunite": 78
        }

    # --------------------------------------------------------
    # AUTRES PAYS INTERESSANTS
    # --------------------------------------------------------

    autres = [
        ("CANADA", CANADA, 55, 85),
        ("SENEGAL", SENEGAL, 55, 68),
        ("SINGAPOUR", SINGAPOUR, 35, 88),
        ("ROYAUME_UNI", ROYAUME_UNI, 45, 85),
        ("DANEMARK", DANEMARK, 40, 90),
        ("SUEDE", SUEDE, 40, 83),
        ("AUTRICHE", AUTRICHE, 45, 80)
    ]

    for pays, mots, geo, opportunite in autres:

        if contient(texte, mots):
            return {
                "pays": pays,
                "zone": pays,
                "pipeline": PIPELINE_INTERNATIONAL,
                "score_geographique": geo,
                "score_opportunite": opportunite
            }

    # --------------------------------------------------------
    # FRANCE GENERIQUE
    # --------------------------------------------------------

    indicateurs_france = [
        "france",
        "cedex"
    ]

    if contient(texte, indicateurs_france):
        return {
            "pays": "FRANCE",
            "zone": "FRANCE_AUTRE",
            "pipeline": PIPELINE_FRANCE,
            "score_geographique": 60,
            "score_opportunite": 75
        }

    # --------------------------------------------------------
    # INCONNU
    # --------------------------------------------------------

    return {
        "pays": "INCONNU",
        "zone": "INCONNUE",
        "pipeline": PIPELINE_INTERNATIONAL,
        "score_geographique": 50,
        "score_opportunite": 50
    }


# ============================================================
# BONUS POUR LE SCORE FINAL
# ============================================================

def calculer_bonus_strategique(zone):
    """
    Bonus volontairement limité.

    Une excellente offre suisse ne doit pas être pénalisée
    simplement parce qu'elle est loin de l'Île-de-France.

    Le bonus favorise les zones préférées mais ne sert jamais
    de critère d'exclusion.
    """

    geo = int(
        zone.get(
            "score_geographique",
            50
        )
    )

    opportunite = int(
        zone.get(
            "score_opportunite",
            50
        )
    )

    # 60 % préférence géographique
    # 40 % potentiel de la zone
    indice = (
        geo * 0.60
        +
        opportunite * 0.40
    )

    if indice >= 92:
        return 8

    if indice >= 85:
        return 6

    if indice >= 75:
        return 4

    if indice >= 65:
        return 2

    if indice >= 55:
        return 1

    return 0


# ============================================================
# ANALYSE STRATEGIQUE COMPLETE
# ============================================================

def analyser_strategie(offre):
    lieu = offre.get(
        "lieu",
        ""
    )

    description = offre.get(
        "description",
        ""
    )

    zone = detecter_zone(
        lieu=lieu,
        description=description
    )

    bonus = calculer_bonus_strategique(
        zone
    )

    resultat = dict(
        zone
    )

    resultat[
        "bonus_strategique"
    ] = bonus

    return resultat