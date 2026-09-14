from core.candidate_facts import (
    obtenir_faits_candidat
)


CV_ATS_PLAN_VERSION = "cv_ats_plan_v1"


# ============================================================
# CHOIX DU TITRE
# ============================================================

def choisir_titre_cv(
    analyse_ats,
    cv_source
):
    titres = analyse_ats.get(
        "titres_cv_possibles",
        []
    )

    if titres:
        return titres[0]

    cv_source = str(
        cv_source
        or ""
    ).upper()

    if cv_source == "TECHNICIEN":
        return "Technicien chimiste"

    if cv_source == "INGENIEUR":
        return "Ingénieur chimiste"

    return "Chimiste"


# ============================================================
# COMPETENCES DE BASE
# ============================================================

def competences_base(
    langue="FR"
):
    faits = obtenir_faits_candidat()

    langue = str(
        langue
        or "FR"
    ).upper()

    cle_langue = (
        "en"
        if langue == "EN"
        else "fr"
    )

    resultat = []

    for competence in (
        faits[
            "competences_confirmees"
        ].values()
    ):

        formulation = competence.get(
            cle_langue
        )

        if formulation:
            resultat.append(
                formulation
            )

    return resultat


# ============================================================
# COMPETENCES PROTEGEES
# ============================================================

def competences_protegees(
    langue="FR"
):
    faits = obtenir_faits_candidat()

    langue = str(
        langue
        or "FR"
    ).upper()

    cle_langue = (
        "en"
        if langue == "EN"
        else "fr"
    )

    resultat = []

    for competence in (
        faits[
            "competences_protegees"
        ].values()
    ):

        formulation = competence.get(
            cle_langue
        )

        if formulation:
            resultat.append(
                formulation
            )

    return resultat


# ============================================================
# CONSTRUCTION DU PLAN
# ============================================================

def construire_plan_cv(
    offre,
    analyse_ats,
    cv_source
):
    langue = str(
        analyse_ats.get(
            "langue_annonce",
            "FR"
        )
        or "FR"
    ).upper()

    titre = choisir_titre_cv(
        analyse_ats,
        cv_source
    )

    competences_offre = analyse_ats.get(
        "competences_confirmees_cv",
        []
    )

    competences_niveau_protege = (
        analyse_ats.get(
            "competences_protegees_cv",
            []
        )
    )

    qualites = analyse_ats.get(
        "qualites_confirmees_cv",
        []
    )

    contextuels = analyse_ats.get(
        "termes_contextuels_a_valider",
        []
    )

    refuses = analyse_ats.get(
        "mots_cles_refuses",
        []
    )

    inconnus = analyse_ats.get(
        "mots_cles_inconnus",
        []
    )

    missions = analyse_ats.get(
        "missions_du_poste",
        []
    )

    formations = analyse_ats.get(
        "formations_possibles_apres_embauche",
        []
    )

    # --------------------------------------------------------
    # COMPETENCES TECHNIQUES DU CANDIDAT
    # --------------------------------------------------------

    base = competences_base(
        langue
    )

    protegees_base = competences_protegees(
        langue
    )

    # Les compétences correspondant explicitement à
    # l'offre passent devant les autres.
    competences_finales = []

    for element in (
        competences_offre
        + base
    ):

        if (
            element
            and element
            not in competences_finales
        ):
            competences_finales.append(
                element
            )

    protegees_finales = []

    for element in (
        competences_niveau_protege
        + protegees_base
    ):

        if (
            element
            and element
            not in protegees_finales
        ):
            protegees_finales.append(
                element
            )

    # --------------------------------------------------------
    # PLAN
    # --------------------------------------------------------

    return {
        "version":
            CV_ATS_PLAN_VERSION,

        "titre_cv":
            titre,

        "cv_source":
            cv_source,

        "pays":
            analyse_ats.get(
                "pays",
                "INCONNU"
            ),

        "langue":
            langue,

        "format_cv":
            analyse_ats.get(
                "format_cv_recommande",
                "CV_FR_ATS"
            ),

        "poste_cible":
            offre.get(
                "titre",
                ""
            ),

        "entreprise":
            offre.get(
                "entreprise",
                ""
            ),

        # ----------------------------------------------------
        # AUTORISE AUTOMATIQUEMENT
        # ----------------------------------------------------

        "competences_confirmees":
            competences_finales,

        "competences_niveau_protege":
            protegees_finales,

        "qualites_confirmees":
            qualites,

        # ----------------------------------------------------
        # PAS D'INSERTION AUTOMATIQUE
        # ----------------------------------------------------

        "validation_humaine":
            contextuels,

        "interdits":
            refuses,

        "inconnus":
            inconnus,

        # ----------------------------------------------------
        # INFORMATIONS SUR L'OFFRE
        # ----------------------------------------------------

        "missions_futures":
            missions,

        "formations_possibles":
            formations,

        # ----------------------------------------------------
        # SECURITE
        # ----------------------------------------------------

        "regles_generation": [
            (
                "Conserver exactement les diplômes, "
                "expériences, entreprises et dates du CV source."
            ),

            (
                "Ne jamais transformer une mission future "
                "de l'offre en expérience passée."
            ),

            (
                "Ne jamais ajouter un élément de la liste "
                "interdits ou inconnus comme compétence."
            ),

            (
                "Les éléments nécessitant validation humaine "
                "ne sont pas ajoutés automatiquement."
            ),

            (
                "HPLC et LC-MS restent uniquement au niveau "
                "défini dans competences_niveau_protege."
            ),

            (
                "Aucune certification, logiciel, technique "
                "ou durée d'expérience ne peut être inventé."
            )
        ],

        "validation_humaine_requise":
            True
    }