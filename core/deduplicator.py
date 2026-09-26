import re
import unicodedata

from difflib import SequenceMatcher
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)


# ============================================================
# NORMALISATION TEXTE
# ============================================================

def normaliser_texte(
    texte
):

    if texte is None:
        return ""

    texte = str(
        texte
    ).strip().lower()

    texte = unicodedata.normalize(
        "NFKD",
        texte,
    )

    texte = "".join(
        caractere
        for caractere in texte
        if not unicodedata.combining(
            caractere
        )
    )

    texte = re.sub(
        r"[^a-z0-9]+",
        " ",
        texte,
    )

    texte = re.sub(
        r"\s+",
        " ",
        texte,
    )

    return texte.strip()


# ============================================================
# SIMILARITE TEXTE
# ============================================================

def similarite_texte(
    texte_a,
    texte_b
):

    a = normaliser_texte(
        texte_a
    )

    b = normaliser_texte(
        texte_b
    )

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(
        None,
        a,
        b,
    ).ratio()


# ============================================================
# ACCES AUX CHAMPS
# ============================================================

def _premiere_valeur(
    offre,
    noms
):

    if not isinstance(
        offre,
        dict,
    ):
        return ""

    for nom in noms:

        valeur = offre.get(
            nom
        )

        if valeur is None:
            continue

        valeur = str(
            valeur
        ).strip()

        if valeur:
            return valeur

    return ""


def _titre(
    offre
):

    return _premiere_valeur(
        offre,
        [
            "titre",
            "title",
            "poste",
        ],
    )


def _entreprise(
    offre
):

    return _premiere_valeur(
        offre,
        [
            "entreprise",
            "company",
            "employeur",
            "employer",
        ],
    )


def _lieu(
    offre
):

    return _premiere_valeur(
        offre,
        [
            "lieu",
            "location",
            "ville",
        ],
    )


def _source(
    offre
):

    return _premiere_valeur(
        offre,
        [
            "source",
        ],
    )


def _source_id(
    offre
):

    return _premiere_valeur(
        offre,
        [
            "source_id",
            "id_source",
            "external_id",
        ],
    )


def _url(
    offre
):

    return _premiere_valeur(
        offre,
        [
            "url_principale",
            "url",
            "lien",
            "link",
        ],
    )


# ============================================================
# NORMALISATION SOURCE
# ============================================================

def _normaliser_source(
    source
):

    source = normaliser_texte(
        source
    )

    if (
        "linkedin"
        in source
    ):
        return "linkedin"

    if (
        "france travail"
        in source
        or "francetravail"
        in source
        or "pole emploi"
        in source
    ):
        return "france_travail"

    if "apec" in source:
        return "apec"

    if "indeed" in source:
        return "indeed"

    return source.replace(
        " ",
        "_",
    )


# ============================================================
# URL
# ============================================================

PARAMETRES_TRACKING = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "trk",
    "trackingid",
    "ref",
    "refid",
    "src",
}


def _normaliser_url(
    url
):

    if not url:
        return ""

    url = str(
        url
    ).strip()

    if not url:
        return ""

    # LinkedIn :
    # on réduit directement l'URL à l'identifiant du job.
    match_linkedin = re.search(
        r"(?:linkedin\.com/)?(?:comm/)?jobs/view/(\d+)",
        url,
        flags=re.IGNORECASE,
    )

    if match_linkedin:

        return (
            "https://www.linkedin.com/jobs/view/"
            f"{match_linkedin.group(1)}/"
        )

    try:

        parties = urlsplit(
            url
        )

    except Exception:

        return url.lower().rstrip(
            "/"
        )

    schema = (
        parties.scheme.lower()
        or "https"
    )

    domaine = (
        parties.netloc
        .lower()
        .strip()
    )

    if domaine.startswith(
        "www."
    ):

        domaine = domaine[
            4:
        ]

    chemin = re.sub(
        r"/+",
        "/",
        parties.path
        or "/",
    )

    if (
        chemin != "/"
        and chemin.endswith(
            "/"
        )
    ):

        chemin = chemin[
            :-1
        ]

    parametres = []

    for cle, valeur in parse_qsl(
        parties.query,
        keep_blank_values=True,
    ):

        if (
            cle.lower()
            in PARAMETRES_TRACKING
        ):
            continue

        if cle.lower().startswith(
            "utm_"
        ):
            continue

        parametres.append(
            (
                cle,
                valeur,
            )
        )

    parametres.sort()

    query = urlencode(
        parametres,
        doseq=True,
    )

    return urlunsplit(
        (
            schema,
            domaine,
            chemin,
            query,
            "",
        )
    ).lower()


# ============================================================
# IDENTIFIANTS FOURNISSEUR
# ============================================================

def _extraire_id_linkedin(
    offre
):

    source = _normaliser_source(
        _source(
            offre
        )
    )

    source_id = _source_id(
        offre
    )

    if (
        source == "linkedin"
        and re.fullmatch(
            r"\d{5,}",
            source_id,
        )
    ):

        return source_id

    url = _url(
        offre
    )

    match = re.search(
        r"(?:comm/)?jobs/view/(\d+)",
        url,
        flags=re.IGNORECASE,
    )

    if match:

        return match.group(
            1
        )

    return ""


def _extraire_id_france_travail(
    offre
):

    source = _normaliser_source(
        _source(
            offre
        )
    )

    source_id = _source_id(
        offre
    )

    if (
        source
        == "france_travail"
        and source_id
    ):

        return (
            source_id
            .strip()
            .upper()
        )

    url = _url(
        offre
    )

    # Exemple :
    # /offres/recherche/detail/213SRFZ
    match = re.search(
        r"/detail/([a-z0-9]+)",
        url,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            match.group(
                1
            )
            .upper()
        )

    return ""


# ============================================================
# DOUBLONS CERTAINS
# ============================================================

def _doublon_source_id(
    offre_a,
    offre_b
):

    source_a = _normaliser_source(
        _source(
            offre_a
        )
    )

    source_b = _normaliser_source(
        _source(
            offre_b
        )
    )

    id_a = _source_id(
        offre_a
    )

    id_b = _source_id(
        offre_b
    )

    if (
        not source_a
        or not source_b
        or not id_a
        or not id_b
    ):

        return False

    return (
        source_a == source_b
        and normaliser_texte(
            id_a
        )
        == normaliser_texte(
            id_b
        )
    )


def _doublon_url(
    offre_a,
    offre_b
):

    url_a = _normaliser_url(
        _url(
            offre_a
        )
    )

    url_b = _normaliser_url(
        _url(
            offre_b
        )
    )

    if not url_a or not url_b:
        return False

    return (
        url_a
        == url_b
    )


def _doublon_identifiant_connu(
    offre_a,
    offre_b
):

    linkedin_a = (
        _extraire_id_linkedin(
            offre_a
        )
    )

    linkedin_b = (
        _extraire_id_linkedin(
            offre_b
        )
    )

    if (
        linkedin_a
        and linkedin_b
        and linkedin_a
        == linkedin_b
    ):

        return True

    ft_a = (
        _extraire_id_france_travail(
            offre_a
        )
    )

    ft_b = (
        _extraire_id_france_travail(
            offre_b
        )
    )

    if (
        ft_a
        and ft_b
        and ft_a
        == ft_b
    ):

        return True

    return False


def _doublon_certain(
    offre_a,
    offre_b
):

    if _doublon_source_id(
        offre_a,
        offre_b,
    ):

        return True

    if _doublon_url(
        offre_a,
        offre_b,
    ):

        return True

    if _doublon_identifiant_connu(
        offre_a,
        offre_b,
    ):

        return True

    return False


# ============================================================
# SCORE FUZZY
# ============================================================

def score_doublon(
    offre_a,
    offre_b
):

    # Les égalités certaines ont toujours priorité
    # sur la comparaison textuelle.
    if _doublon_certain(
        offre_a,
        offre_b,
    ):

        return 1.0

    titre_a = _titre(
        offre_a
    )

    titre_b = _titre(
        offre_b
    )

    entreprise_a = _entreprise(
        offre_a
    )

    entreprise_b = _entreprise(
        offre_b
    )

    lieu_a = _lieu(
        offre_a
    )

    lieu_b = _lieu(
        offre_b
    )

    # Sans titre des deux côtés, pas de dédoublonnage
    # fuzzy fiable.
    if (
        not titre_a
        or not titre_b
    ):

        return 0.0

    sim_titre = similarite_texte(
        titre_a,
        titre_b,
    )

    sim_entreprise = similarite_texte(
        entreprise_a,
        entreprise_b,
    )

    sim_lieu = similarite_texte(
        lieu_a,
        lieu_b,
    )

    # Protection contre les faux positifs :
    # deux entreprises clairement différentes ne doivent
    # normalement pas fusionner juste parce que le titre
    # est "Technicien chimiste".
    if (
        entreprise_a
        and entreprise_b
        and sim_entreprise < 0.35
    ):

        return min(
            0.69,
            sim_titre * 0.65,
        )

    elements = [
        (
            sim_titre,
            0.60,
            bool(
                titre_a
                and titre_b
            ),
        ),
        (
            sim_entreprise,
            0.25,
            bool(
                entreprise_a
                and entreprise_b
            ),
        ),
        (
            sim_lieu,
            0.15,
            bool(
                lieu_a
                and lieu_b
            ),
        ),
    ]

    total = 0.0
    poids_total = 0.0

    for score, poids, disponible in elements:

        if not disponible:
            continue

        total += (
            score
            * poids
        )

        poids_total += poids

    if poids_total <= 0:
        return 0.0

    resultat = (
        total
        / poids_total
    )

    return max(
        0.0,
        min(
            1.0,
            resultat,
        ),
    )


# ============================================================
# DECISION
# ============================================================

def sont_doublons(
    offre_a,
    offre_b,
    seuil=0.78,
):

    if _doublon_certain(
        offre_a,
        offre_b,
    ):

        return True

    score = score_doublon(
        offre_a,
        offre_b,
    )

    return (
        score >= seuil
    )


# ============================================================
# QUALITE D'UNE OFFRE
# ============================================================

def _score_completude(
    offre
):

    score = 0

    champs = [
        "titre",
        "entreprise",
        "lieu",
        "contrat",
        "description",
        "date_publication",
        "experience",
        "salaire",
        "url",
        "url_principale",
        "source_id",
    ]

    for champ in champs:

        valeur = offre.get(
            champ
        )

        if valeur:

            score += 1

    description = str(
        offre.get(
            "description",
            ""
        )
        or ""
    )

    # Une vraie fiche complète est préférable
    # à une simple carte d'alerte.
    if len(
        description
    ) >= 300:

        score += 3

    if len(
        description
    ) >= 1000:

        score += 2

    return score


# ============================================================
# FUSION CONSERVATRICE
# ============================================================

def _fusionner_offres(
    offre_existante,
    nouvelle_offre
):

    # On garde comme base l'offre la plus complète.
    if (
        _score_completude(
            nouvelle_offre
        )
        > _score_completude(
            offre_existante
        )
    ):

        principale = dict(
            nouvelle_offre
        )

        secondaire = (
            offre_existante
        )

    else:

        principale = dict(
            offre_existante
        )

        secondaire = (
            nouvelle_offre
        )

    # On ne remplace que les champs vides.
    # Aucun contenu existant n'est écrasé aveuglément.
    for cle, valeur in secondaire.items():

        if cle not in principale:

            principale[
                cle
            ] = valeur

            continue

        valeur_actuelle = principale.get(
            cle
        )

        if (
            valeur_actuelle is None
            or valeur_actuelle == ""
            or valeur_actuelle == []
            or valeur_actuelle == {}
        ):

            principale[
                cle
            ] = valeur

    return principale


# ============================================================
# DEDOUBLONNAGE GLOBAL
# ============================================================

def dedoublonner_offres(
    offres,
    seuil=0.78,
):

    if not offres:
        return []

    uniques = []

    for offre in offres:

        if not isinstance(
            offre,
            dict,
        ):

            continue

        index_doublon = None

        for index, existante in enumerate(
            uniques
        ):

            if sont_doublons(
                existante,
                offre,
                seuil=seuil,
            ):

                index_doublon = (
                    index
                )

                break

        if index_doublon is None:

            uniques.append(
                dict(
                    offre
                )
            )

        else:

            uniques[
                index_doublon
            ] = _fusionner_offres(
                uniques[
                    index_doublon
                ],
                offre,
            )

    return uniques