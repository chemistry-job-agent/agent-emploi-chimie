from copy import deepcopy

from core.candidate_facts import (
    CANDIDATE_FACTS_VERSION,
    securiser_mots_cles,
    verifier_formulation
)


ATS_GUARD_VERSION = "ats_guard_v2"


# ============================================================
# SECURISATION DES PREUVES IA
# ============================================================

def securiser_criteres(criteres):
    resultat = []
    preuves_bloquees = []

    for critere in criteres:

        copie = deepcopy(
            critere
        )

        statut = str(
            copie.get(
                "statut",
                ""
            )
        ).upper()

        preuve = str(
            copie.get(
                "preuve",
                ""
            )
            or ""
        )

        copie[
            "preuve_validee"
        ] = True

        # On contrôle surtout les affirmations positives.
        # Une preuve ABSENT peut légitimement citer
        # une compétence que le candidat ne possède pas.
        if statut in {
            "CONFIRME",
            "PARTIEL"
        }:

            controle = verifier_formulation(
                preuve
            )

            if not controle[
                "valide"
            ]:

                copie[
                    "preuve_brute"
                ] = preuve

                termes = []

                for probleme in controle[
                    "problemes"
                ]:

                    terme = probleme.get(
                        "texte",
                        ""
                    )

                    if (
                        terme
                        and terme not in termes
                    ):
                        termes.append(
                            terme
                        )

                copie[
                    "preuve"
                ] = (
                    "Preuve IA bloquée automatiquement : "
                    "elle contient une formulation ou "
                    "un terme non confirmé."
                )

                copie[
                    "preuve_validee"
                ] = False

                preuves_bloquees.append(
                    {
                        "critere":
                            copie.get(
                                "terme",
                                ""
                            ),

                        "termes":
                            termes,

                        "preuve_brute":
                            preuve
                    }
                )

        resultat.append(
            copie
        )

    return (
        resultat,
        preuves_bloquees
    )


# ============================================================
# EXTRACTION DES ABSENCES
# ============================================================

def extraire_absents(criteres):
    resultat = []

    for critere in criteres:

        statut = str(
            critere.get(
                "statut",
                ""
            )
        ).upper()

        if statut != "ABSENT":
            continue

        terme = str(
            critere.get(
                "terme",
                ""
            )
            or ""
        ).strip()

        if (
            terme
            and terme not in resultat
        ):
            resultat.append(
                terme
            )

    return resultat


# ============================================================
# ADAPTATIONS CV SECURISEES
# ============================================================

def construire_adaptations(
    securite,
    analyse
):
    adaptations = []

    competences = securite.get(
        "competences_confirmees",
        []
    )

    proteges = securite.get(
        "competences_protegees",
        []
    )

    qualites = securite.get(
        "qualites_confirmees",
        []
    )

    intitules = securite.get(
        "intitules_cibles",
        []
    )

    contextuels = securite.get(
        "contextuels",
        []
    )

    refuses = securite.get(
        "refuses",
        []
    )

    inconnus = securite.get(
        "inconnus",
        []
    )

    # --------------------------------------------------------
    # INTITULES
    # --------------------------------------------------------

    if intitules:

        adaptations.append(
            "Peut servir comme intitulé cible du CV, "
            "sans prétendre avoir déjà occupé ce poste : "
            + ", ".join(
                intitules
            )
            + "."
        )

    # --------------------------------------------------------
    # COMPETENCES CONFIRMEES
    # --------------------------------------------------------

    if competences:

        adaptations.append(
            "Compétences confirmées pouvant être mises "
            "davantage en évidence lorsque pertinentes : "
            + ", ".join(
                competences
            )
            + "."
        )

    # --------------------------------------------------------
    # QUALITES
    # --------------------------------------------------------

    if qualites:

        adaptations.append(
            "Qualités ou compétences transversales "
            "confirmées pouvant être mises en avant : "
            + ", ".join(
                qualites
            )
            + "."
        )

    # --------------------------------------------------------
    # NIVEAU PROTEGE
    # --------------------------------------------------------

    if proteges:

        adaptations.append(
            "Ces techniques peuvent apparaître uniquement "
            "avec leur niveau réel exact : "
            + ", ".join(
                proteges
            )
            + "."
        )

    # --------------------------------------------------------
    # CONTEXTUELS
    # --------------------------------------------------------

    if contextuels:

        adaptations.append(
            "Ces termes sont contextuels et nécessitent "
            "une preuve ou une validation humaine avant "
            "d'être présentés comme compétences : "
            + ", ".join(
                contextuels
            )
            + "."
        )

    # --------------------------------------------------------
    # REFUSES
    # --------------------------------------------------------

    if refuses:

        adaptations.append(
            "Ne jamais présenter automatiquement comme "
            "compétences acquises : "
            + ", ".join(
                refuses
            )
            + "."
        )

    # --------------------------------------------------------
    # INCONNUS
    # --------------------------------------------------------

    if inconnus:

        adaptations.append(
            "Ces termes ne sont pas classés dans la base "
            "de faits candidat et nécessitent une "
            "validation humaine : "
            + ", ".join(
                inconnus
            )
            + "."
        )

    # --------------------------------------------------------
    # FORMATIONS APRES EMBAUCHE
    # --------------------------------------------------------

    formations = analyse.get(
        "formations_possibles_apres_embauche",
        []
    )

    if formations:

        adaptations.append(
            "Peuvent uniquement être présentées comme "
            "formations à acquérir ou disponibilité "
            "à se former : "
            + ", ".join(
                formations
            )
            + "."
        )

    # --------------------------------------------------------
    # MISSIONS FUTURES
    # --------------------------------------------------------

    missions = analyse.get(
        "missions_du_poste",
        []
    )

    if missions:

        adaptations.append(
            "Les missions prévues par l'offre ne doivent "
            "jamais être transformées en expériences "
            "professionnelles déjà réalisées."
        )

    return adaptations


# ============================================================
# RESUME DETERMINISTE
# ============================================================

def construire_resume(
    analyse,
    securite,
    manques_reels,
    bonus_absents,
    preuves_bloquees
):
    score = analyse.get(
        "score_ats_contenu",
        0
    )

    competences = len(
        securite.get(
            "competences_confirmees",
            []
        )
    )

    proteges = len(
        securite.get(
            "competences_protegees",
            []
        )
    )

    qualites = len(
        securite.get(
            "qualites_confirmees",
            []
        )
    )

    intitules = len(
        securite.get(
            "intitules_cibles",
            []
        )
    )

    contextuels = len(
        securite.get(
            "contextuels",
            []
        )
    )

    refuses = len(
        securite.get(
            "refuses",
            []
        )
    )

    inconnus = len(
        securite.get(
            "inconnus",
            []
        )
    )

    return (
        f"Score ATS contenu : {score}/100. "
        f"{competences} compétence(s) confirmée(s), "
        f"{proteges} compétence(s) à formulation protégée, "
        f"{qualites} qualité(s) confirmée(s), "
        f"{intitules} intitulé(s) cible(s) autorisé(s), "
        f"{contextuels} terme(s) contextuel(s) nécessitant "
        f"une validation, "
        f"{refuses} terme(s) explicitement non confirmés "
        f"et {inconnus} terme(s) inconnus. "
        f"{len(manques_reels)} manque(s) réellement "
        f"obligatoire(s) ou important(s), "
        f"{len(bonus_absents)} critère(s) bonus absent(s). "
        f"{len(preuves_bloquees)} preuve(s) générée(s) par "
        f"l'IA ont été bloquées par le garde-fou."
    )


# ============================================================
# GARDE-FOU COMPLET
# ============================================================

def securiser_analyse_ats(analyse):
    resultat = deepcopy(
        analyse
    )

    langue = str(
        resultat.get(
            "langue_annonce",
            "FR"
        )
        or "FR"
    ).upper()

    mots_cles = resultat.get(
        "mots_cles_ats",
        []
    )

    # --------------------------------------------------------
    # CLASSIFICATION SELON LA SOURCE DE VERITE
    # --------------------------------------------------------

    securite = securiser_mots_cles(
        mots_cles,
        langue=langue
    )

    # --------------------------------------------------------
    # SECURISATION DES PREUVES IA
    # --------------------------------------------------------

    toutes_preuves_bloquees = []

    for cle in [
        "criteres_eliminatoires",
        "criteres_importants",
        "criteres_bonus"
    ]:

        (
            criteres_securises,
            preuves_bloquees
        ) = securiser_criteres(
            resultat.get(
                cle,
                []
            )
        )

        resultat[
            cle
        ] = criteres_securises

        toutes_preuves_bloquees.extend(
            preuves_bloquees
        )

    # --------------------------------------------------------
    # MANQUES REELS
    # --------------------------------------------------------

    manques_reels = []

    for cle in [
        "criteres_eliminatoires",
        "criteres_importants"
    ]:

        for terme in extraire_absents(
            resultat.get(
                cle,
                []
            )
        ):

            if terme not in manques_reels:
                manques_reels.append(
                    terme
                )

    bonus_absents = extraire_absents(
        resultat.get(
            "criteres_bonus",
            []
        )
    )

    # --------------------------------------------------------
    # RESULTATS SECURISES
    # --------------------------------------------------------

    resultat[
        "competences_confirmees_cv"
    ] = securite[
        "competences_confirmees"
    ]

    resultat[
        "competences_protegees_cv"
    ] = securite[
        "competences_protegees"
    ]

    resultat[
        "qualites_confirmees_cv"
    ] = securite[
        "qualites_confirmees"
    ]

    resultat[
        "intitules_cibles_autorises"
    ] = securite[
        "intitules_cibles"
    ]

    resultat[
        "termes_contextuels_a_valider"
    ] = securite[
        "contextuels"
    ]

    resultat[
        "mots_cles_refuses"
    ] = securite[
        "refuses"
    ]

    resultat[
        "mots_cles_inconnus"
    ] = securite[
        "inconnus"
    ]

    # --------------------------------------------------------
    # CE QUE LE FUTUR GENERATEUR POURRA UTILISER
    # AUTOMATIQUEMENT DANS LES SECTIONS DE COMPETENCES
    # --------------------------------------------------------

    resultat[
        "mots_cles_a_integrer"
    ] = (
        securite[
            "competences_confirmees"
        ]
        +
        securite[
            "competences_protegees"
        ]
        +
        securite[
            "qualites_confirmees"
        ]
    )

    # Le titre du CV est volontairement séparé.
    resultat[
        "titres_cv_possibles"
    ] = securite[
        "intitules_cibles"
    ]

    # Rien de cette liste ne pourra être ajouté
    # automatiquement au CV.
    resultat[
        "interdits_insertion_automatique"
    ] = (
        securite[
            "contextuels"
        ]
        +
        securite[
            "refuses"
        ]
        +
        securite[
            "inconnus"
        ]
    )

    resultat[
        "termes_a_nuancer"
    ] = securite[
        "competences_protegees"
    ]

    resultat[
        "manques_reels"
    ] = manques_reels

    resultat[
        "bonus_absents"
    ] = bonus_absents

    resultat[
        "preuves_bloquees"
    ] = toutes_preuves_bloquees

    # --------------------------------------------------------
    # ADAPTATIONS
    # --------------------------------------------------------

    resultat[
        "adaptations_cv"
    ] = construire_adaptations(
        securite,
        resultat
    )

    # --------------------------------------------------------
    # RESUME
    # --------------------------------------------------------

    resultat[
        "resume_ats"
    ] = construire_resume(
        resultat,
        securite,
        manques_reels,
        bonus_absents,
        toutes_preuves_bloquees
    )

    # --------------------------------------------------------
    # METADONNEES
    # --------------------------------------------------------

    resultat[
        "candidate_facts_version"
    ] = CANDIDATE_FACTS_VERSION

    resultat[
        "ats_guard_version"
    ] = ATS_GUARD_VERSION

    resultat[
        "garde_fou_anti_invention"
    ] = True

    resultat[
        "validation_humaine_requise"
    ] = True

    return resultat