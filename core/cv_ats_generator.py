import json

from pathlib import Path

from core.candidate_facts import (
    verifier_formulation
)

from core.cv_loader import (
    charger_cvs
)


CV_ATS_GENERATOR_VERSION = "cv_ats_generator_v1"


# ============================================================
# ACCROCHE DETERMINISTE
# ============================================================

def construire_accroche(
    cv_source,
    langue
):
    cv_source = str(
        cv_source
        or ""
    ).upper()

    langue = str(
        langue
        or "FR"
    ).upper()

    if langue == "EN":

        if cv_source == "TECHNICIEN":

            return (
                "Master's degree graduate in Biomolecular Chemistry "
                "with research internship experience in organic "
                "synthesis and laboratory work. Skills include "
                "organic synthesis, reaction monitoring, purification, "
                "chromatography, 1D/2D NMR, IR, UV-Vis and TLC. "
                "Basic knowledge of HPLC and LC-MS limited to "
                "results interpretation."
            )

        return (
            "Master's degree graduate in Biomolecular Chemistry "
            "with research internship experience in organic synthesis. "
            "Skills include multi-step synthesis, reaction monitoring, "
            "purification, chromatography, 1D/2D NMR, IR, UV-Vis "
            "and TLC. Basic knowledge of HPLC and LC-MS limited "
            "to results interpretation."
        )

    if cv_source == "TECHNICIEN":

        return (
            "Titulaire d’un Master 2 Chimie des Biomolécules, "
            "avec des expériences de stage en synthèse organique "
            "et en laboratoire de recherche. Compétences en "
            "synthèse organique, suivi de réaction, purification, "
            "chromatographie, RMN 1D/2D, IR, UV-Vis et CCM. "
            "Notions en HPLC et LC-MS limitées à "
            "l’interprétation des résultats."
        )

    return (
        "Titulaire d’un Master 2 Chimie des Biomolécules, "
        "avec des expériences de stage en synthèse organique. "
        "Compétences en synthèse multi-étapes, suivi de réaction, "
        "purification, chromatographie, RMN 1D/2D, IR, UV-Vis "
        "et CCM. Notions en HPLC et LC-MS limitées à "
        "l’interprétation des résultats."
    )


# ============================================================
# CHARGEMENT DU CV SOURCE
# ============================================================

def charger_cv_source(
    type_cv
):
    cvs = charger_cvs()

    type_cv = str(
        type_cv
        or ""
    ).upper()

    if type_cv not in cvs:

        raise ValueError(
            f"CV source inconnu : {type_cv}"
        )

    return cvs[
        type_cv
    ]


# ============================================================
# DEDUPLICATION
# ============================================================

def dedupliquer(elements):
    resultat = []

    for element in elements:

        element = str(
            element
            or ""
        ).strip()

        if (
            element
            and element not in resultat
        ):
            resultat.append(
                element
            )

    return resultat


# ============================================================
# CONSTRUCTION DU BROUILLON
# ============================================================

def construire_brouillon_cv(
    offre,
    plan
):
    cv_source_type = str(
        plan.get(
            "cv_source",
            ""
        )
    ).upper()

    cv_source = charger_cv_source(
        cv_source_type
    )

    texte_cv_source = cv_source.get(
        "texte",
        ""
    )

    langue = str(
        plan.get(
            "langue",
            "FR"
        )
    ).upper()

    titre = str(
        plan.get(
            "titre_cv",
            "Chimiste"
        )
    ).strip()

    accroche = construire_accroche(
        cv_source_type,
        langue
    )

    competences = dedupliquer(
        plan.get(
            "competences_confirmees",
            []
        )
    )

    protegees = dedupliquer(
        plan.get(
            "competences_niveau_protege",
            []
        )
    )

    qualites = dedupliquer(
        plan.get(
            "qualites_confirmees",
            []
        )
    )

    # --------------------------------------------------------
    # SECURITE DU CONTENU GENERE
    # --------------------------------------------------------

    contenu_nouveau = (
        titre
        + "\n"
        + accroche
        + "\n"
        + "\n".join(
            competences
        )
        + "\n"
        + "\n".join(
            protegees
        )
        + "\n"
        + "\n".join(
            qualites
        )
    )

    controle = verifier_formulation(
        contenu_nouveau
    )

    if not controle[
        "valide"
    ]:

        raise RuntimeError(
            "Le garde-fou a refusé le contenu "
            f"du CV : {controle['problemes']}"
        )

    return {
        "version":
            CV_ATS_GENERATOR_VERSION,

        "offre_id":
            offre.get(
                "id"
            ),

        "entreprise":
            offre.get(
                "entreprise",
                ""
            ),

        "poste":
            offre.get(
                "titre",
                ""
            ),

        "pays":
            plan.get(
                "pays",
                ""
            ),

        "langue":
            langue,

        "format_cv":
            plan.get(
                "format_cv",
                ""
            ),

        "cv_source_type":
            cv_source_type,

        "cv_source_path":
            cv_source.get(
                "chemin",
                ""
            ),

        "titre_cv":
            titre,

        "accroche":
            accroche,

        "competences":
            competences,

        "competences_protegees":
            protegees,

        "qualites":
            qualites,

        # ----------------------------------------------------
        # ELEMENTS JAMAIS AJOUTES AUTOMATIQUEMENT
        # ----------------------------------------------------

        "validation_humaine":
            plan.get(
                "validation_humaine",
                []
            ),

        "interdits":
            plan.get(
                "interdits",
                []
            ),

        "inconnus":
            plan.get(
                "inconnus",
                []
            ),

        # ----------------------------------------------------
        # LE CV ORIGINAL RESTE LA SOURCE DE VERITE
        # ----------------------------------------------------

        "texte_cv_source":
            texte_cv_source,

        "validation_garde_fou":
            True,

        "validation_humaine_requise":
            True
    }


# ============================================================
# TEXTE ATS LISIBLE
# ============================================================

def rendre_brouillon_texte(
    brouillon
):
    langue = brouillon[
        "langue"
    ]

    lignes = []

    lignes.append(
        brouillon[
            "titre_cv"
        ].upper()
    )

    lignes.append(
        ""
    )

    if langue == "EN":

        lignes.append(
            "PROFESSIONAL SUMMARY"
        )

    else:

        lignes.append(
            "PROFIL"
        )

    lignes.append(
        "=" * 60
    )

    lignes.append(
        brouillon[
            "accroche"
        ]
    )

    lignes.append(
        ""
    )

    if langue == "EN":

        lignes.append(
            "TECHNICAL SKILLS"
        )

    else:

        lignes.append(
            "COMPÉTENCES TECHNIQUES"
        )

    lignes.append(
        "=" * 60
    )

    for competence in brouillon[
        "competences"
    ]:

        lignes.append(
            f"- {competence}"
        )

    for competence in brouillon[
        "competences_protegees"
    ]:

        lignes.append(
            f"- {competence}"
        )

    if brouillon[
        "qualites"
    ]:

        lignes.append(
            ""
        )

        if langue == "EN":

            lignes.append(
                "ADDITIONAL SKILLS"
            )

        else:

            lignes.append(
                "COMPÉTENCES TRANSVERSALES"
            )

        lignes.append(
            "=" * 60
        )

        for qualite in brouillon[
            "qualites"
        ]:

            lignes.append(
                f"- {qualite}"
            )

    lignes.append(
        ""
    )

    lignes.append(
        "SOURCE CV ORIGINALE - "
        "EXPÉRIENCES / FORMATION À CONSERVER"
    )

    lignes.append(
        "=" * 60
    )

    lignes.append(
        brouillon[
            "texte_cv_source"
        ]
    )

    return "\n".join(
        lignes
    )


# ============================================================
# SAUVEGARDE
# ============================================================

def sauvegarder_brouillon(
    brouillon,
    dossier
):
    dossier = Path(
        dossier
    )

    dossier.mkdir(
        parents=True,
        exist_ok=True
    )

    offre_id = brouillon[
        "offre_id"
    ]

    chemin_json = (
        dossier
        / f"cv_ats_offre_{offre_id}_draft.json"
    )

    chemin_txt = (
        dossier
        / f"cv_ats_offre_{offre_id}_draft.txt"
    )

    chemin_json.write_text(
        json.dumps(
            brouillon,
            ensure_ascii=False,
            indent=2,
            default=str
        ),
        encoding="utf-8"
    )

    chemin_txt.write_text(
        rendre_brouillon_texte(
            brouillon
        ),
        encoding="utf-8"
    )

    return {
        "json":
            str(
                chemin_json
            ),

        "txt":
            str(
                chemin_txt
            )
    }