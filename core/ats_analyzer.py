import json
import re
import time
import unicodedata

from pathlib import Path

import ollama

from core.cv_loader import charger_cvs
from core.strategy import analyser_strategie


# ============================================================
# CONFIGURATION
# ============================================================

MODELE = "gpt-oss:20b"

ATS_ANALYSE_VERSION = "ats_v2"

PROFIL_PATH = Path(
    "profil.json"
)


# ============================================================
# OUTILS
# ============================================================

def normaliser_texte(texte):
    texte = str(
        texte
        or ""
    ).lower().strip()

    texte = unicodedata.normalize(
        "NFKD",
        texte
    )

    texte = "".join(
        caractere
        for caractere in texte
        if not unicodedata.combining(
            caractere
        )
    )

    texte = texte.replace(
        "-",
        "-"
    )

    texte = texte.replace(
        "–",
        "-"
    )

    texte = re.sub(
        r"[^a-z0-9+#]+",
        " ",
        texte
    )

    texte = re.sub(
        r"\s+",
        " ",
        texte
    )

    return texte.strip()


def dedupliquer_liste(elements):
    resultat = []
    vus = set()

    for element in elements:

        element = str(
            element
            or ""
        ).strip()

        if not element:
            continue

        cle = normaliser_texte(
            element
        )

        if cle in vus:
            continue

        vus.add(
            cle
        )

        resultat.append(
            element
        )

    return resultat


def charger_profil():
    if not PROFIL_PATH.exists():
        raise FileNotFoundError(
            "profil.json introuvable."
        )

    return json.loads(
        PROFIL_PATH.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# LANGUE
# ============================================================

def detecter_langue(
    titre="",
    description=""
):
    texte = normaliser_texte(
        f"{titre} {description}"
    )

    mots_fr = [
        "vous",
        "votre",
        "poste",
        "missions",
        "experience",
        "competences",
        "chimie",
        "laboratoire",
        "candidat",
        "formation"
    ]

    mots_en = [
        "you",
        "your",
        "role",
        "job",
        "experience",
        "skills",
        "chemistry",
        "laboratory",
        "candidate",
        "degree",
        "responsibilities"
    ]

    mots_de = [
        "sie",
        "ihre",
        "chemie",
        "labor",
        "erfahrung",
        "kenntnisse",
        "aufgaben",
        "abschluss",
        "bewerbung"
    ]

    scores = {
        "FR": sum(
            1
            for mot in mots_fr
            if re.search(
                rf"\b{re.escape(mot)}\b",
                texte
            )
        ),

        "EN": sum(
            1
            for mot in mots_en
            if re.search(
                rf"\b{re.escape(mot)}\b",
                texte
            )
        ),

        "DE": sum(
            1
            for mot in mots_de
            if re.search(
                rf"\b{re.escape(mot)}\b",
                texte
            )
        )
    }

    meilleur = max(
        scores,
        key=scores.get
    )

    if scores[
        meilleur
    ] == 0:
        return "INCONNUE"

    return meilleur


# ============================================================
# FORMAT CV
# ============================================================

def recommander_format_cv(
    pays,
    langue
):
    pays = str(
        pays
        or "INCONNU"
    ).upper()

    langue = str(
        langue
        or "INCONNUE"
    ).upper()

    if pays == "CANADA":

        if langue == "FR":
            return "CV_CANADA_FR_ATS"

        return "RESUME_CANADA_EN_ATS"

    if pays == "SUISSE":

        if langue == "DE":
            return "CV_SUISSE_DE_ATS"

        if langue == "EN":
            return "CV_SUISSE_EN_ATS"

        return "CV_SUISSE_FR_ATS"

    if pays == "ALLEMAGNE":

        if langue == "DE":
            return "CV_ALLEMAGNE_DE_ATS"

        return "CV_INTERNATIONAL_EN_ATS"

    if pays in {
        "ARABIE_SAOUDITE",
        "EMIRATS_ARABES_UNIS",
        "QATAR",
        "OMAN",
        "IRLANDE",
        "SINGAPOUR",
        "ROYAUME_UNI",
        "DANEMARK",
        "SUEDE",
        "PAYS_BAS"
    }:
        return "CV_INTERNATIONAL_EN_ATS"

    if pays in {
        "FRANCE",
        "BELGIQUE",
        "LUXEMBOURG",
        "ALGERIE",
        "SENEGAL"
    }:

        if langue == "EN":
            return "CV_INTERNATIONAL_EN_ATS"

        return "CV_FR_ATS"

    if langue == "DE":
        return "CV_DE_ATS"

    if langue == "EN":
        return "CV_INTERNATIONAL_EN_ATS"

    return "CV_FR_ATS"


# ============================================================
# GROUPES DE SYNONYMES AUTORISES
# ============================================================

GROUPES_ALIAS = [
    [
        "rmn",
        "nmr"
    ],

    [
        "ccm",
        "tlc"
    ],

    [
        "synthese organique",
        "organic synthesis"
    ],

    [
        "chromatographie",
        "chromatography"
    ],

    [
        "purification",
        "purification techniques"
    ],

    [
        "recristallisation",
        "recrystallization"
    ],

    [
        "ir",
        "infrared",
        "infra red"
    ],

    [
        "uv vis",
        "uv visible",
        "uv-vis"
    ],

    [
        "hplc",
        "high performance liquid chromatography"
    ],

    [
        "lc ms",
        "lc-ms",
        "liquid chromatography mass spectrometry"
    ],

    [
        "laboratoire",
        "laboratory"
    ],

    [
        "chimie",
        "chemistry"
    ],

    [
        "rigoureux",
        "rigueur",
        "rigorous"
    ]
]


# ============================================================
# COMPETENCES A NIVEAU PROTEGE
# ============================================================

TERMES_PROTEGES = {
    normaliser_texte(
        "HPLC"
    ): (
        "HPLC — notions / interprétation "
        "des résultats"
    ),

    normaliser_texte(
        "LC-MS"
    ): (
        "LC-MS — notions / interprétation "
        "des résultats"
    )
}


# ============================================================
# CORPUS DE PREUVE
# ============================================================

def construire_corpus(
    profil,
    texte_cv
):
    profil_texte = json.dumps(
        profil,
        ensure_ascii=False,
        default=str
    )

    return normaliser_texte(
        profil_texte
        + " "
        + str(
            texte_cv
            or ""
        )
    )


def trouver_aliases(
    terme
):
    terme_normalise = normaliser_texte(
        terme
    )

    for groupe in GROUPES_ALIAS:

        groupe_normalise = [
            normaliser_texte(
                element
            )
            for element in groupe
        ]

        if any(
            alias == terme_normalise
            or alias in terme_normalise
            or terme_normalise in alias
            for alias in groupe_normalise
        ):
            return groupe_normalise

    return [
        terme_normalise
    ]


def terme_est_prouve(
    terme,
    corpus
):
    terme_normalise = normaliser_texte(
        terme
    )

    if not terme_normalise:
        return False, ""

    # Correspondance directe
    if terme_normalise in corpus:
        return True, terme_normalise

    # Synonymes sûrs
    aliases = trouver_aliases(
        terme
    )

    for alias in aliases:

        if alias and alias in corpus:
            return True, alias

    return False, ""


# ============================================================
# DETECTION DES TERMES PROTEGES
# ============================================================

def identifier_terme_protege(
    terme
):
    terme_normalise = normaliser_texte(
        terme
    )

    for cle, formulation in (
        TERMES_PROTEGES.items()
    ):

        if (
            cle == terme_normalise
            or cle in terme_normalise
        ):
            return formulation

    return None


# ============================================================
# SECURISATION DES MOTS-CLES
# ============================================================

def securiser_mots_cles(
    mots_cles,
    corpus
):
    autorises = []
    proteges = []
    non_prouves = []
    details = []

    for terme in dedupliquer_liste(
        mots_cles
    ):

        prouve, preuve = terme_est_prouve(
            terme,
            corpus
        )

        formulation_protegee = (
            identifier_terme_protege(
                terme
            )
        )

        if (
            prouve
            and formulation_protegee
        ):

            proteges.append(
                formulation_protegee
            )

            details.append(
                {
                    "terme": terme,
                    "statut":
                        "NIVEAU_PROTEGE",

                    "preuve":
                        preuve,

                    "formulation_autorisee":
                        formulation_protegee
                }
            )

            continue

        if prouve:

            autorises.append(
                terme
            )

            details.append(
                {
                    "terme":
                        terme,

                    "statut":
                        "AUTORISE",

                    "preuve":
                        preuve,

                    "formulation_autorisee":
                        terme
                }
            )

            continue

        non_prouves.append(
            terme
        )

        details.append(
            {
                "terme":
                    terme,

                "statut":
                    "NON_PROUVE",

                "preuve":
                    "",

                "formulation_autorisee":
                    ""
            }
        )

    autorises = dedupliquer_liste(
        autorises
    )

    proteges = dedupliquer_liste(
        proteges
    )

    non_prouves = dedupliquer_liste(
        non_prouves
    )

    return {
        "mots_cles_autorises":
            autorises,

        "mots_cles_niveau_protege":
            proteges,

        "mots_cles_non_prouves":
            non_prouves,

        "details_mots_cles":
            details
    }


# ============================================================
# SCHEMA GPT
# ============================================================

CRITERE_SCHEMA = {
    "type": "object",

    "properties": {

        "terme": {
            "type": "string"
        },

        "statut": {
            "type": "string",

            "enum": [
                "CONFIRME",
                "PARTIEL",
                "ABSENT"
            ]
        },

        "preuve": {
            "type": "string"
        }
    },

    "required": [
        "terme",
        "statut",
        "preuve"
    ]
}


ANALYSE_SCHEMA = {
    "type": "object",

    "properties": {

        "criteres_eliminatoires": {
            "type": "array",
            "items": CRITERE_SCHEMA
        },

        "criteres_importants": {
            "type": "array",
            "items": CRITERE_SCHEMA
        },

        "criteres_bonus": {
            "type": "array",
            "items": CRITERE_SCHEMA
        },

        "missions_du_poste": {
            "type": "array",

            "items": {
                "type": "string"
            }
        },

        "formations_possibles_apres_embauche": {
            "type": "array",

            "items": {
                "type": "string"
            }
        },

        "mots_cles_ats": {
            "type": "array",

            "items": {
                "type": "string"
            }
        },

        "risques_ats": {
            "type": "array",

            "items": {
                "type": "string"
            }
        },

        "commentaire_global": {
            "type": "string"
        }
    },

    "required": [
        "criteres_eliminatoires",
        "criteres_importants",
        "criteres_bonus",
        "missions_du_poste",
        "formations_possibles_apres_embauche",
        "mots_cles_ats",
        "risques_ats",
        "commentaire_global"
    ]
}


# ============================================================
# SCORE
# ============================================================

def calculer_couverture(
    exigences
):
    if not exigences:
        return None

    total = 0.0

    for exigence in exigences:

        statut = str(
            exigence.get(
                "statut",
                "ABSENT"
            )
        ).upper()

        if statut == "CONFIRME":
            total += 1.0

        elif statut == "PARTIEL":
            total += 0.5

    return (
        total
        / len(
            exigences
        )
    )


def compter_absents(
    exigences
):
    return sum(
        1
        for exigence in exigences
        if str(
            exigence.get(
                "statut",
                ""
            )
        ).upper() == "ABSENT"
    )


def calculer_score_ats(
    analyse,
    securite_mots_cles
):
    eliminatoires = analyse.get(
        "criteres_eliminatoires",
        []
    )

    importants = analyse.get(
        "criteres_importants",
        []
    )

    bonus = analyse.get(
        "criteres_bonus",
        []
    )

    couverture_eliminatoire = (
        calculer_couverture(
            eliminatoires
        )
    )

    couverture_importante = (
        calculer_couverture(
            importants
        )
    )

    couverture_bonus = (
        calculer_couverture(
            bonus
        )
    )

    groupes = []

    if couverture_eliminatoire is not None:
        groupes.append(
            (
                couverture_eliminatoire,
                0.55
            )
        )

    if couverture_importante is not None:
        groupes.append(
            (
                couverture_importante,
                0.35
            )
        )

    if couverture_bonus is not None:
        groupes.append(
            (
                couverture_bonus,
                0.10
            )
        )

    if not groupes:
        score_exigences = 0

    else:

        poids_total = sum(
            poids
            for _, poids in groupes
        )

        score_exigences = round(
            100
            * sum(
                couverture
                * (
                    poids
                    / poids_total
                )
                for couverture, poids
                in groupes
            )
        )

    # --------------------------------------------------------
    # VISIBILITE DES MOTS-CLES REELLEMENT PROUVES
    # --------------------------------------------------------

    nb_autorises = len(
        securite_mots_cles[
            "mots_cles_autorises"
        ]
    )

    nb_proteges = len(
        securite_mots_cles[
            "mots_cles_niveau_protege"
        ]
    )

    nb_non_prouves = len(
        securite_mots_cles[
            "mots_cles_non_prouves"
        ]
    )

    total_mots_cles = (
        nb_autorises
        + nb_proteges
        + nb_non_prouves
    )

    if total_mots_cles:

        score_mots_cles = round(
            100
            * (
                nb_autorises
                + nb_proteges
            )
            / total_mots_cles
        )

    else:
        score_mots_cles = 0

    # --------------------------------------------------------
    # ATS CONTENU
    # --------------------------------------------------------

    score_ats = round(
        (
            score_exigences
            * 0.80
        )
        +
        (
            score_mots_cles
            * 0.20
        )
    )

    absents_eliminatoires = compter_absents(
        eliminatoires
    )

    if absents_eliminatoires == 1:
        score_ats = min(
            score_ats,
            60
        )

    elif absents_eliminatoires >= 2:
        score_ats = min(
            score_ats,
            45
        )

    score_ats = max(
        0,
        min(
            100,
            int(
                score_ats
            )
        )
    )

    if score_ats >= 85:
        niveau = "EXCELLENT"

    elif score_ats >= 72:
        niveau = "BON"

    elif score_ats >= 58:
        niveau = "MOYEN"

    else:
        niveau = "FAIBLE"

    return {
        "score_compatibilite_exigences":
            score_exigences,

        "score_visibilite_mots_cles":
            score_mots_cles,

        "score_ats_contenu":
            score_ats,

        "niveau_ats":
            niveau,

        # Compatibilité avec tester_ats.py V1
        "couverture_obligatoire":
            None
            if couverture_eliminatoire is None
            else round(
                couverture_eliminatoire
                * 100
            ),

        "couverture_importante":
            None
            if couverture_importante is None
            else round(
                couverture_importante
                * 100
            ),

        "couverture_bonus":
            None
            if couverture_bonus is None
            else round(
                couverture_bonus
                * 100
            ),

        "nb_obligatoires_absents":
            absents_eliminatoires
    }


# ============================================================
# MANQUES REELS
# ============================================================

def extraire_manques_reels(
    analyse
):
    manques = []

    for categorie in [
        "criteres_eliminatoires",
        "criteres_importants"
    ]:

        for critere in analyse.get(
            categorie,
            []
        ):

            if str(
                critere.get(
                    "statut",
                    ""
                )
            ).upper() == "ABSENT":

                terme = critere.get(
                    "terme",
                    ""
                )

                if terme:
                    manques.append(
                        terme
                    )

    return dedupliquer_liste(
        manques
    )


# ============================================================
# ADAPTATIONS SECURISEES
# ============================================================

def construire_adaptations_securisees(
    securite,
    analyse
):
    adaptations = []

    autorises = securite[
        "mots_cles_autorises"
    ]

    proteges = securite[
        "mots_cles_niveau_protege"
    ]

    non_prouves = securite[
        "mots_cles_non_prouves"
    ]

    if autorises:

        adaptations.append(
            "Mettre davantage en évidence, "
            "si pertinent dans les bonnes sections du CV : "
            + ", ".join(
                autorises[
                    :12
                ]
            )
            + "."
        )

    if proteges:

        adaptations.append(
            "Conserver strictement les niveaux réels : "
            + ", ".join(
                proteges
            )
            + "."
        )

    if non_prouves:

        adaptations.append(
            "Ne pas ajouter comme compétences acquises "
            "sans preuve : "
            + ", ".join(
                non_prouves[
                    :15
                ]
            )
            + "."
        )

    formations = analyse.get(
        "formations_possibles_apres_embauche",
        []
    )

    if formations:

        adaptations.append(
            "Les éléments suivants peuvent être présentés "
            "comme formations à acquérir ou disponibilité "
            "à se former, mais jamais comme certifications "
            "déjà obtenues : "
            + ", ".join(
                formations[
                    :10
                ]
            )
            + "."
        )

    missions = analyse.get(
        "missions_du_poste",
        []
    )

    if missions:

        adaptations.append(
            "Ne pas transformer les missions futures "
            "du poste en expériences passées du candidat."
        )

    return adaptations


# ============================================================
# RESUME SECURISE
# ============================================================

def construire_resume_securise(
    analyse,
    score,
    securite
):
    nb_eliminatoires = len(
        analyse.get(
            "criteres_eliminatoires",
            []
        )
    )

    nb_importants = len(
        analyse.get(
            "criteres_importants",
            []
        )
    )

    absents = score[
        "nb_obligatoires_absents"
    ]

    autorises = len(
        securite[
            "mots_cles_autorises"
        ]
    )

    proteges = len(
        securite[
            "mots_cles_niveau_protege"
        ]
    )

    non_prouves = len(
        securite[
            "mots_cles_non_prouves"
        ]
    )

    return (
        f"Score ATS contenu : "
        f"{score['score_ats_contenu']}/100. "
        f"{nb_eliminatoires} critère(s) réellement "
        f"éliminatoire(s) identifié(s), dont "
        f"{absents} absent(s). "
        f"{nb_importants} critère(s) important(s). "
        f"{autorises} mot(s)-clé(s) peuvent être "
        f"mis en avant sur preuve directe, "
        f"{proteges} terme(s) nécessitent un niveau "
        f"de formulation protégé, et "
        f"{non_prouves} terme(s) ne doivent pas être "
        f"ajoutés automatiquement au CV. "
        f"Les missions futures et formations disponibles "
        f"après embauche ne sont pas traitées comme "
        f"des compétences déjà acquises."
    )


# ============================================================
# CHARGEMENT CV
# ============================================================

def charger_cv_selectionne(
    cv_recommande
):
    cvs = charger_cvs()

    cv_recommande = str(
        cv_recommande
        or ""
    ).upper()

    if cv_recommande not in cvs:

        raise ValueError(
            "CV recommandé invalide : "
            f"{cv_recommande}"
        )

    return cvs[
        cv_recommande
    ]


# ============================================================
# ANALYSE ATS
# ============================================================

def analyser_ats(
    offre,
    cv_recommande
):
    profil = charger_profil()

    cv = charger_cv_selectionne(
        cv_recommande
    )

    texte_cv = cv.get(
        "texte",
        ""
    )

    corpus = construire_corpus(
        profil,
        texte_cv
    )

    strategie = analyser_strategie(
        offre
    )

    pays = strategie.get(
        "pays",
        "INCONNU"
    )

    langue = detecter_langue(
        titre=offre.get(
            "titre",
            ""
        ),

        description=offre.get(
            "description",
            ""
        )
    )

    format_cv = recommander_format_cv(
        pays,
        langue
    )

    offre_json = json.dumps(
        offre,
        ensure_ascii=False,
        indent=2,
        default=str
    )

    profil_json = json.dumps(
        profil,
        ensure_ascii=False,
        indent=2,
        default=str
    )

    prompt = f"""
Tu analyses une candidature pour un système ATS.

Tu ne rédiges PAS le CV.
Tu classes correctement les exigences de l'offre.

============================================================
REGLES ABSOLUES
============================================================

Aucune invention.

Une mission du poste n'est PAS automatiquement une
expérience préalable exigée.

Exemple :
"vous assurerez la réception des déchets"
est une MISSION DU POSTE sauf si l'annonce exige
explicitement une expérience préalable dans cette activité.

Une compétence ou certification que l'employeur indique
pouvoir faire acquérir après l'embauche doit aller dans :

formations_possibles_apres_embauche

et PAS dans les critères éliminatoires.

Un critère n'est "éliminatoire" que si l'annonce indique
clairement qu'il est obligatoire avant l'embauche.

Un diplôme supérieur peut satisfaire un niveau minimum.

Exemple :
Bac+5 peut satisfaire une demande Bac+2 en chimie,
sauf indication explicite contraire.

Statuts :

CONFIRME
= preuve réelle et suffisante.

PARTIEL
= notions, compétence transférable ou expérience proche.

ABSENT
= aucune preuve.

Concernant HPLC et LC-MS :
ne jamais parler de maîtrise autonome sans preuve.
Le niveau autorisé reste notions / interprétation des
résultats si c'est ce qui apparaît dans le profil.

Ne jamais inventer :
5S,
CACES,
ADR,
BSD,
HECATE,
gestion des déchets,
GC-MS,
ou toute autre compétence absente des sources.

Ne confonds pas :
- compétence requise ;
- mission future ;
- formation accessible après embauche.

============================================================
PAYS / LANGUE
============================================================

Pays :
{pays}

Langue :
{langue}

Format CV :
{format_cv}

============================================================
PROFIL
============================================================

{profil_json}

============================================================
CV
============================================================

{texte_cv}

============================================================
OFFRE
============================================================

{offre_json}

============================================================
SORTIE
============================================================

Classe les informations dans :

1. criteres_eliminatoires
2. criteres_importants
3. criteres_bonus
4. missions_du_poste
5. formations_possibles_apres_embauche
6. mots_cles_ats
7. risques_ats
8. commentaire_global

Les mots_cles_ats doivent provenir de l'offre.

Ne décide pas quels mots-clés seront ajoutés au CV :
un garde-fou Python fera cette vérification ensuite.
"""

    debut = time.time()

    derniere_erreur = None

    for tentative in range(
        1,
        3
    ):

        try:

            reponse = ollama.chat(
                model=MODELE,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                format=ANALYSE_SCHEMA,

                think="low",

                options={
                    "temperature": 0,
                    "num_ctx": 12288
                },

                keep_alive="30m"
            )

            contenu = (
                reponse[
                    "message"
                ][
                    "content"
                ]
                .strip()
            )

            if not contenu:
                raise ValueError(
                    "Réponse GPT vide."
                )

            analyse = json.loads(
                contenu
            )

            # ------------------------------------------------
            # NORMALISATION DES LISTES
            # ------------------------------------------------

            analyse[
                "missions_du_poste"
            ] = dedupliquer_liste(
                analyse.get(
                    "missions_du_poste",
                    []
                )
            )

            analyse[
                "formations_possibles_apres_embauche"
            ] = dedupliquer_liste(
                analyse.get(
                    "formations_possibles_apres_embauche",
                    []
                )
            )

            analyse[
                "mots_cles_ats"
            ] = dedupliquer_liste(
                analyse.get(
                    "mots_cles_ats",
                    []
                )
            )

            # ------------------------------------------------
            # PARE-FEU PYTHON
            # ------------------------------------------------

            securite = securiser_mots_cles(
                analyse[
                    "mots_cles_ats"
                ],
                corpus
            )

            score = calculer_score_ats(
                analyse,
                securite
            )

            manques = extraire_manques_reels(
                analyse
            )

            adaptations = (
                construire_adaptations_securisees(
                    securite,
                    analyse
                )
            )

            resume_securise = (
                construire_resume_securise(
                    analyse,
                    score,
                    securite
                )
            )

            # ------------------------------------------------
            # COMPATIBILITE AVEC ATS V1
            # ------------------------------------------------

            analyse[
                "exigences_obligatoires"
            ] = analyse.get(
                "criteres_eliminatoires",
                []
            )

            analyse[
                "exigences_importantes"
            ] = analyse.get(
                "criteres_importants",
                []
            )

            analyse[
                "exigences_bonus"
            ] = analyse.get(
                "criteres_bonus",
                []
            )

            analyse[
                "mots_cles_a_integrer"
            ] = dedupliquer_liste(
                securite[
                    "mots_cles_autorises"
                ]
                +
                securite[
                    "mots_cles_niveau_protege"
                ]
            )

            analyse[
                "termes_a_nuancer"
            ] = securite[
                "mots_cles_niveau_protege"
            ]

            analyse[
                "termes_non_prouves"
            ] = securite[
                "mots_cles_non_prouves"
            ]

            analyse[
                "manques_reels"
            ] = manques

            analyse[
                "adaptations_cv"
            ] = adaptations

            # ------------------------------------------------
            # SCORE
            # ------------------------------------------------

            analyse.update(
                score
            )

            analyse.update(
                securite
            )

            # ------------------------------------------------
            # RESUMES
            # ------------------------------------------------

            analyse[
                "resume_ats_gpt_brut"
            ] = analyse.get(
                "commentaire_global",
                ""
            )

            analyse[
                "resume_ats"
            ] = resume_securise

            # ------------------------------------------------
            # METADONNEES
            # ------------------------------------------------

            analyse[
                "pays"
            ] = pays

            analyse[
                "langue_annonce"
            ] = langue

            analyse[
                "format_cv_recommande"
            ] = format_cv

            analyse[
                "pipeline"
            ] = strategie.get(
                "pipeline",
                "INTERNATIONAL"
            )

            analyse[
                "cv_source"
            ] = str(
                cv_recommande
            ).upper()

            analyse[
                "fichier_cv_source"
            ] = cv.get(
                "chemin",
                ""
            )

            analyse[
                "modele"
            ] = MODELE

            analyse[
                "ats_analyse_version"
            ] = ATS_ANALYSE_VERSION

            analyse[
                "garde_fou_anti_invention"
            ] = True

            analyse[
                "temps_ats_secondes"
            ] = round(
                time.time()
                - debut,
                1
            )

            return analyse

        except Exception as erreur:

            derniere_erreur = erreur

            print(
                f"Tentative ATS "
                f"{tentative}/2 échouée : "
                f"{erreur}"
            )

    raise RuntimeError(
        "Analyse ATS impossible : "
        f"{derniere_erreur}"
    )