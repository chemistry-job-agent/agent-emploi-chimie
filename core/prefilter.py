from core.deduplicator import normaliser_texte


MOTS_FORTS = [
    "chimiste",
    "chimie organique",
    "synthese organique",
    "organic chemist",
    "synthetic chemist",
    "research chemist",
    "r d chimie",
    "ingenieur chimiste",
    "ingenieur chimie",
    "technicien chimiste",
    "assistant ingenieur chimie",
    "analyste chimiste",
    "process chemist",
]


MOTS_METIERS = [
    "ingenieur",
    "technicien",
    "chimiste",
    "scientist",
    "research associate",
    "research assistant",
    "analyste",
    "assistant ingenieur",
    "charge d etudes",
    "charge de developpement",
]


MOTS_CHIMIE = [
    "chimie",
    "synthese",
    "organique",
    "laboratoire",
    "r d",
    "recherche",
    "developpement",
    "analytique",
    "pharmaceutique",
    "pharma",
    "chimie fine",
    "molecule",
    "biomolecule",
    "purification",
    "chromatographie",
    "hplc",
    "lc ms",
    "rmn",
    "spectroscopie",
    "formulation",
    "process",
    "procede",
]


EXCLUSIONS_TITRE = [
    "ingenieur commercial",
    "technico commercial",
    "commercial itinerant",
    "commercial terrain",
    "business developer",
    "business development manager",
    "sales engineer",
    "sales representative",
    "account manager",
    "professeur",
    "enseignant",
    "formateur",
    "doctorant",
    "these cifre",
    "stage ",
    "stagiaire",
    "alternance",
    "alternant",
]


SENIORITE_FORTE = [
    "directeur",
    "director",
    "head of",
    "responsable de site",
    "vice president",
    "vp ",
]


def contient_un(
    texte,
    expressions
):

    return any(
        expression in texte
        for expression in expressions
    )


def evaluer_prefiltre(
    offre
):

    titre = normaliser_texte(
        offre.get(
            "titre",
            ""
        )
    )

    description = normaliser_texte(
        offre.get(
            "description",
            ""
        )
    )

    contrat = normaliser_texte(
        offre.get(
            "contrat",
            ""
        )
    )

    lieu = normaliser_texte(
        offre.get(
            "lieu",
            ""
        )
    )

    texte_complet = (
        titre
        + " "
        + description[:5000]
    )

    score = 0
    raisons = []
    exclusions = []


    # ==========================================
    # EXCLUSIONS ÉVIDENTES
    # ==========================================

    if contient_un(
        titre,
        EXCLUSIONS_TITRE
    ):

        exclusions.append(
            "Intitulé clairement hors cible"
        )


    if contient_un(
        titre,
        SENIORITE_FORTE
    ):

        score -= 15

        raisons.append(
            "Niveau de séniorité élevé"
        )


    # ==========================================
    # CORRESPONDANCE FORTE
    # ==========================================

    for mot in MOTS_FORTS:

        if mot in texte_complet:

            score += 10

            raisons.append(
                f"Correspondance forte : {mot}"
            )

            break


    # ==========================================
    # TYPE DE POSTE
    # ==========================================

    if contient_un(
        titre,
        MOTS_METIERS
    ):

        score += 8

        raisons.append(
            "Type de poste pertinent"
        )


    # ==========================================
    # VOCABULAIRE CHIMIE
    # ==========================================

    nombre_mots_chimie = sum(
        1
        for mot in MOTS_CHIMIE
        if mot in texte_complet
    )

    score += min(
        nombre_mots_chimie * 3,
        18
    )

    if nombre_mots_chimie:

        raisons.append(
            f"{nombre_mots_chimie} "
            f"indice(s) technique(s) chimie"
        )


    # ==========================================
    # SYNTHÈSE ORGANIQUE
    # ==========================================

    if (
        "synthese organique"
        in texte_complet
        or
        "chimie organique"
        in texte_complet
        or
        "organic chemistry"
        in texte_complet
    ):

        score += 12

        raisons.append(
            "Très forte proximité avec "
            "la synthèse organique"
        )


    # ==========================================
    # R&D / LABORATOIRE
    # ==========================================

    if (
        "r d" in texte_complet
        or
        "recherche" in texte_complet
        or
        "laboratoire" in texte_complet
    ):

        score += 6

        raisons.append(
            "Environnement R&D/laboratoire"
        )


    # ==========================================
    # CONTRAT
    # ==========================================

    if "cdi" in contrat:

        score += 6

        raisons.append(
            "CDI"
        )

    elif "cdd" in contrat:

        score += 2

        raisons.append(
            "CDD"
        )

    elif (
        "interim" in contrat
        or
        "interimaire" in contrat
    ):

        score -= 2

        raisons.append(
            "Intérim"
        )


    # ==========================================
    # LOCALISATION PRIORITAIRE
    # ==========================================

    if (
        "montpellier" in lieu
        or
        "castelnau le lez" in lieu
    ):

        score += 5

        raisons.append(
            "Zone prioritaire Montpellier"
        )

    elif (
        "paris" in lieu
        or
        "ile de france" in lieu
    ):

        score += 5

        raisons.append(
            "Zone prioritaire Paris/IDF"
        )


    # ==========================================
    # DÉCISION
    # ==========================================

    rejet_dur = len(
        exclusions
    ) > 0

    seuil = 18

    passer = (
        not rejet_dur
        and score >= seuil
    )


    return {
        "score_prefiltre":
            score,

        "passer":
            passer,

        "rejet_dur":
            rejet_dur,

        "raisons":
            raisons,

        "exclusions":
            exclusions
    }


def prefiltrer_offres(
    offres,
    seuil=18
):

    retenues = []
    rejetees = []


    for offre in offres:

        analyse = evaluer_prefiltre(
            offre
        )

        # Permet de modifier le seuil
        # depuis le programme principal.

        passer = (
            not analyse["rejet_dur"]
            and
            analyse["score_prefiltre"]
            >= seuil
        )

        offre["_score_prefiltre"] = (
            analyse["score_prefiltre"]
        )

        offre["_prefiltre_raisons"] = (
            analyse["raisons"]
        )

        offre["_prefiltre_exclusions"] = (
            analyse["exclusions"]
        )


        if passer:

            retenues.append(
                offre
            )

        else:

            rejetees.append(
                offre
            )


    retenues.sort(
        key=lambda offre:
            offre.get(
                "_score_prefiltre",
                0
            ),
        reverse=True
    )


    return retenues, rejetees