import re
import unicodedata


# ============================================================
# VERSION
# ============================================================

CANDIDATE_FACTS_VERSION = "candidate_facts_v2"


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


def contient_expression(
    texte,
    expression
):
    """
    Recherche une expression complète.

    Evite par exemple :
    IR -> risques industriels
    CAP -> capacité
    """

    texte = normaliser_texte(
        texte
    )

    expression = normaliser_texte(
        expression
    )

    if not texte or not expression:
        return False

    motif = (
        r"(?:^|\s)"
        + re.escape(
            expression
        )
        + r"(?:\s|$)"
    )

    return (
        re.search(
            motif,
            texte
        )
        is not None
    )


# ============================================================
# FORMATION
# ============================================================

FORMATION = {
    "niveau":
        "BAC+5",

    "diplome_principal":
        "Master 2 Chimie des Biomolécules",

    "licence":
        "Licence de chimie"
}


# ============================================================
# LANGUES
# ============================================================

LANGUES = {
    "francais":
        "Professionnel",

    "anglais":
        "B1"
}


# ============================================================
# COMPETENCES TECHNIQUES CONFIRMEES
# ============================================================

COMPETENCES_CONFIRMEES = {
    "synthese_organique": {
        "fr":
            "Synthèse organique",

        "en":
            "Organic synthesis",

        "aliases": [
            "synthese organique",
            "organic synthesis"
        ]
    },

    "synthese_multi_etapes": {
        "fr":
            "Synthèse multi-étapes",

        "en":
            "Multi-step synthesis",

        "aliases": [
            "synthese multi etapes",
            "multi step synthesis",
            "multistep synthesis"
        ]
    },

    "suivi_reaction": {
        "fr":
            "Suivi de réaction",

        "en":
            "Reaction monitoring",

        "aliases": [
            "suivi de reaction",
            "reaction monitoring"
        ]
    },

    "purification": {
        "fr":
            "Purification",

        "en":
            "Purification",

        "aliases": [
            "purification"
        ]
    },

    "chromatographie": {
        "fr":
            "Chromatographie",

        "en":
            "Chromatography",

        "aliases": [
            "chromatographie",
            "chromatography"
        ]
    },

    "recristallisation": {
        "fr":
            "Recristallisation",

        "en":
            "Recrystallization",

        "aliases": [
            "recristallisation",
            "recrystallization"
        ]
    },

    "ccm": {
        "fr":
            "CCM",

        "en":
            "TLC",

        "aliases": [
            "ccm",
            "tlc",
            "chromatographie sur couche mince",
            "thin layer chromatography"
        ]
    },

    "rmn": {
        "fr":
            "RMN 1D/2D",

        "en":
            "1D/2D NMR",

        "aliases": [
            "rmn",
            "nmr",
            "rmn 1d",
            "rmn 2d",
            "nmr 1d",
            "nmr 2d",
            "1d 2d nmr"
        ]
    },

    "ir": {
        "fr":
            "IR",

        "en":
            "IR spectroscopy",

        "aliases": [
            "ir",
            "infrared spectroscopy",
            "ir spectroscopy"
        ]
    },

    "uv_vis": {
        "fr":
            "UV-Vis",

        "en":
            "UV-Vis spectroscopy",

        "aliases": [
            "uv vis",
            "uv visible",
            "uv vis spectroscopy"
        ]
    }
}


# ============================================================
# COMPETENCES A NIVEAU PROTEGE
# ============================================================

COMPETENCES_PROTEGEES = {
    "hplc": {
        "fr":
            "Notions en HPLC "
            "(interprétation des résultats)",

        "en":
            "Basic knowledge of HPLC "
            "(results interpretation)",

        "aliases": [
            "hplc",
            "high performance liquid chromatography"
        ]
    },

    "lc_ms": {
        "fr":
            "Notions en LC-MS "
            "(interprétation des résultats)",

        "en":
            "Basic knowledge of LC-MS "
            "(results interpretation)",

        "aliases": [
            "lc ms",
            "liquid chromatography mass spectrometry"
        ]
    }
}


# ============================================================
# QUALITES / COMPETENCES TRANSVERSALES CONFIRMEES
# ============================================================

QUALITES_CONFIRMEES = {
    "rigueur": {
        "fr":
            "Rigueur",

        "en":
            "Rigorous work",

        "aliases": [
            "rigueur",
            "rigoureux",
            "rigoureuse",
            "rigorous"
        ]
    },

    "travail_equipe": {
        "fr":
            "Travail en équipe",

        "en":
            "Teamwork",

        "aliases": [
            "travail en equipe",
            "travail d equipe",
            "teamwork",
            "team work"
        ]
    },

    "rapports_scientifiques": {
        "fr":
            "Rédaction de rapports scientifiques",

        "en":
            "Scientific report writing",

        "aliases": [
            "rapport",
            "rapports",
            "rapport scientifique",
            "rapports scientifiques",
            "scientific report",
            "scientific reports"
        ]
    },

    "presentations_scientifiques": {
        "fr":
            "Présentations scientifiques",

        "en":
            "Scientific presentations",

        "aliases": [
            "presentation scientifique",
            "presentations scientifiques",
            "scientific presentation",
            "scientific presentations"
        ]
    }
}


# ============================================================
# INTITULES CIBLES
# ============================================================

# Important :
# ces intitulés peuvent servir comme TITRE CIBLE du CV.
#
# Cela ne signifie PAS que le candidat prétend avoir déjà
# occupé le poste.

INTITULES_CIBLES = {
    "technicien_chimiste": {
        "fr":
            "Technicien chimiste",

        "en":
            "Chemistry Laboratory Technician",

        "aliases": [
            "technicien chimiste",
            "technicienne chimiste"
        ]
    },

    "technicien_rd_chimie": {
        "fr":
            "Technicien R&D Chimie",

        "en":
            "R&D Chemistry Technician",

        "aliases": [
            "technicien r d chimie",
            "technicien rd chimie",
            "r d chemistry technician"
        ]
    },

    "technicien_laboratoire": {
        "fr":
            "Technicien de laboratoire en chimie",

        "en":
            "Chemistry Laboratory Technician",

        "aliases": [
            "technicien laboratoire chimie",
            "technicien de laboratoire chimie",
            "chemistry laboratory technician"
        ]
    },

    "assistant_ingenieur": {
        "fr":
            "Assistant ingénieur chimie",

        "en":
            "Assistant Chemistry Engineer",

        "aliases": [
            "assistant ingenieur chimie",
            "assistant chemistry engineer"
        ]
    },

    "ingenieur_chimiste": {
        "fr":
            "Ingénieur chimiste",

        "en":
            "Chemist / Chemistry Engineer",

        "aliases": [
            "ingenieur chimiste",
            "ingenieur chimie",
            "chemistry engineer"
        ]
    },

    "chimiste_rd": {
        "fr":
            "Chimiste R&D",

        "en":
            "R&D Chemist",

        "aliases": [
            "chimiste r d",
            "chimiste rd",
            "r d chemist"
        ]
    },

    "chimiste_organicien": {
        "fr":
            "Chimiste organicien",

        "en":
            "Organic Chemist",

        "aliases": [
            "chimiste organicien",
            "organic chemist"
        ]
    },

    "chimiste_synthese": {
        "fr":
            "Chimiste en synthèse organique",

        "en":
            "Organic Synthesis Chemist",

        "aliases": [
            "chimiste synthese",
            "chimiste en synthese organique",
            "organic synthesis chemist"
        ]
    }
}


# ============================================================
# TERMES CONTEXTUELS
# ============================================================

# Ces termes ne sont ni automatiquement vrais ni
# automatiquement faux.
#
# Ils nécessitent une preuve précise avant d'être ajoutés
# comme compétence au CV.

TERMES_CONTEXTUELS = {
    "qualite": [
        "qualite",
        "quality"
    ],

    "securite": [
        "securite",
        "safety"
    ],

    "environnement": [
        "environnement",
        "environment"
    ],

    "pesee": [
        "pesee",
        "weighing"
    ],

    "documentation": [
        "documentation"
    ],

    "conformite": [
        "conformite",
        "compliance"
    ],

    "stock": [
        "stock",
        "stocks",
        "inventory"
    ],

    "expedition": [
        "expedition",
        "shipping"
    ],

    "manutention": [
        "manutention",
        "handling"
    ],

    "risques_industriels": [
        "risques industriels",
        "industrial risks"
    ]
}


# ============================================================
# TERMES EXPLICITEMENT NON CONFIRMES
# ============================================================

TERMES_NON_CONFIRMES = {
    "gc_ms": [
        "gc ms",
        "gas chromatography mass spectrometry"
    ],

    "caces": [
        "caces",
        "caces 3"
    ],

    "adr": [
        "adr",
        "formation adr"
    ],

    "hecate": [
        "hecate",
        "logiciel hecate"
    ],

    "bsd": [
        "bsd",
        "bordereau de suivi des dechets"
    ],

    "fid_dechets": [
        "fid"
    ],

    "cap_dechets": [
        "cap"
    ],

    "5s": [
        "5s",
        "methode 5s"
    ],

    "gestion_dechets": [
        "gestion des dechets",
        "waste management"
    ],

    "engins_manutention": [
        "engins de manutention",
        "manutention d engins"
    ]
}


# ============================================================
# FORMULATIONS FORMELLEMENT INTERDITES
# ============================================================

FORMULATIONS_INTERDITES = [
    "maitrise hplc",
    "maitrise de la hplc",
    "expert hplc",
    "autonome en hplc",

    "maitrise lc ms",
    "maitrise de la lc ms",
    "expert lc ms",
    "autonome en lc ms",

    "maitrise gc ms",
    "maitrise de la gc ms",
    "expert gc ms",

    "certifie caces",
    "certification caces",

    "certifie adr",
    "certification adr"
]


# ============================================================
# RECHERCHE GENERIQUE
# ============================================================

def rechercher_dictionnaire(
    terme,
    dictionnaire
):
    terme_normalise = normaliser_texte(
        terme
    )

    if not terme_normalise:
        return None

    for cle, donnees in (
        dictionnaire.items()
    ):

        aliases = donnees.get(
            "aliases",
            []
        )

        for alias in aliases:

            if contient_expression(
                terme_normalise,
                alias
            ):

                return {
                    "cle":
                        cle,

                    "donnees":
                        donnees
                }

    return None


def rechercher_aliases_simples(
    terme,
    dictionnaire
):
    terme_normalise = normaliser_texte(
        terme
    )

    if not terme_normalise:
        return None

    for cle, aliases in (
        dictionnaire.items()
    ):

        for alias in aliases:

            if contient_expression(
                terme_normalise,
                alias
            ):

                return {
                    "cle":
                        cle
                }

    return None


# ============================================================
# CLASSIFICATION
# ============================================================

def classifier_terme(
    terme
):
    # --------------------------------------------------------
    # INTITULE CIBLE
    # --------------------------------------------------------

    resultat = rechercher_dictionnaire(
        terme,
        INTITULES_CIBLES
    )

    if resultat:

        return {
            "cle":
                resultat["cle"],

            "niveau":
                "INTITULE_CIBLE",

            "formulation_fr":
                resultat[
                    "donnees"
                ][
                    "fr"
                ],

            "formulation_en":
                resultat[
                    "donnees"
                ][
                    "en"
                ]
        }

    # --------------------------------------------------------
    # COMPETENCE PROTEGEE
    # --------------------------------------------------------

    resultat = rechercher_dictionnaire(
        terme,
        COMPETENCES_PROTEGEES
    )

    if resultat:

        return {
            "cle":
                resultat["cle"],

            "niveau":
                "PROTEGE",

            "formulation_fr":
                resultat[
                    "donnees"
                ][
                    "fr"
                ],

            "formulation_en":
                resultat[
                    "donnees"
                ][
                    "en"
                ]
        }

    # --------------------------------------------------------
    # COMPETENCE CONFIRMEE
    # --------------------------------------------------------

    resultat = rechercher_dictionnaire(
        terme,
        COMPETENCES_CONFIRMEES
    )

    if resultat:

        return {
            "cle":
                resultat["cle"],

            "niveau":
                "CONFIRME",

            "formulation_fr":
                resultat[
                    "donnees"
                ][
                    "fr"
                ],

            "formulation_en":
                resultat[
                    "donnees"
                ][
                    "en"
                ]
        }

    # --------------------------------------------------------
    # QUALITE CONFIRMEE
    # --------------------------------------------------------

    resultat = rechercher_dictionnaire(
        terme,
        QUALITES_CONFIRMEES
    )

    if resultat:

        return {
            "cle":
                resultat["cle"],

            "niveau":
                "QUALITE_CONFIRMEE",

            "formulation_fr":
                resultat[
                    "donnees"
                ][
                    "fr"
                ],

            "formulation_en":
                resultat[
                    "donnees"
                ][
                    "en"
                ]
        }

    # --------------------------------------------------------
    # NON CONFIRME
    # --------------------------------------------------------

    resultat = rechercher_aliases_simples(
        terme,
        TERMES_NON_CONFIRMES
    )

    if resultat:

        return {
            "cle":
                resultat["cle"],

            "niveau":
                "NON_CONFIRME"
        }

    # --------------------------------------------------------
    # CONTEXTUEL
    # --------------------------------------------------------

    resultat = rechercher_aliases_simples(
        terme,
        TERMES_CONTEXTUELS
    )

    if resultat:

        return {
            "cle":
                resultat["cle"],

            "niveau":
                "CONTEXTUEL"
        }

    # --------------------------------------------------------
    # INCONNU
    # --------------------------------------------------------

    return {
        "cle":
            None,

        "niveau":
            "INCONNU"
    }


# ============================================================
# FORMULATION AUTORISEE
# ============================================================

def obtenir_formulation_autorisee(
    terme,
    langue="FR"
):
    resultat = classifier_terme(
        terme
    )

    niveau = resultat[
        "niveau"
    ]

    if niveau not in {
        "CONFIRME",
        "PROTEGE",
        "QUALITE_CONFIRMEE",
        "INTITULE_CIBLE"
    }:
        return None

    langue = str(
        langue
        or "FR"
    ).upper()

    if langue == "EN":
        return resultat.get(
            "formulation_en"
        )

    return resultat.get(
        "formulation_fr"
    )


# ============================================================
# SECURISATION MOTS-CLES
# ============================================================

def securiser_mots_cles(
    mots_cles,
    langue="FR"
):
    competences = []
    proteges = []
    qualites = []
    intitules = []
    contextuels = []
    refuses = []
    inconnus = []

    for terme in mots_cles:

        resultat = classifier_terme(
            terme
        )

        niveau = resultat[
            "niveau"
        ]

        formulation = (
            obtenir_formulation_autorisee(
                terme,
                langue
            )
        )

        if (
            niveau == "CONFIRME"
            and formulation
        ):
            competences.append(
                formulation
            )

        elif (
            niveau == "PROTEGE"
            and formulation
        ):
            proteges.append(
                formulation
            )

        elif (
            niveau == "QUALITE_CONFIRMEE"
            and formulation
        ):
            qualites.append(
                formulation
            )

        elif (
            niveau == "INTITULE_CIBLE"
            and formulation
        ):
            intitules.append(
                formulation
            )

        elif niveau == "CONTEXTUEL":

            contextuels.append(
                terme
            )

        elif niveau == "NON_CONFIRME":

            refuses.append(
                terme
            )

        else:

            inconnus.append(
                terme
            )

    return {
        "competences_confirmees":
            list(
                dict.fromkeys(
                    competences
                )
            ),

        "competences_protegees":
            list(
                dict.fromkeys(
                    proteges
                )
            ),

        "qualites_confirmees":
            list(
                dict.fromkeys(
                    qualites
                )
            ),

        "intitules_cibles":
            list(
                dict.fromkeys(
                    intitules
                )
            ),

        "contextuels":
            list(
                dict.fromkeys(
                    contextuels
                )
            ),

        "refuses":
            list(
                dict.fromkeys(
                    refuses
                )
            ),

        "inconnus":
            list(
                dict.fromkeys(
                    inconnus
                )
            )
    }


# ============================================================
# VERIFICATION D'UN TEXTE GENERE
# ============================================================

def verifier_formulation(
    texte
):
    texte_normalise = normaliser_texte(
        texte
    )

    problemes = []

    # --------------------------------------------------------
    # FORMULATIONS INTERDITES
    # --------------------------------------------------------

    for formulation in (
        FORMULATIONS_INTERDITES
    ):

        if contient_expression(
            texte_normalise,
            formulation
        ):

            problemes.append(
                {
                    "type":
                        "FORMULATION_INTERDITE",

                    "texte":
                        formulation
                }
            )

    # --------------------------------------------------------
    # TERMES NON CONFIRMES
    # --------------------------------------------------------

    for cle, aliases in (
        TERMES_NON_CONFIRMES.items()
    ):

        for alias in aliases:

            if contient_expression(
                texte_normalise,
                alias
            ):

                problemes.append(
                    {
                        "type":
                            "TERME_NON_CONFIRME",

                        "cle":
                            cle,

                        "texte":
                            alias
                    }
                )

                break

    return {
        "valide":
            len(
                problemes
            ) == 0,

        "problemes":
            problemes
    }


# ============================================================
# EXPORT DES FAITS
# ============================================================

def obtenir_faits_candidat():
    return {
        "version":
            CANDIDATE_FACTS_VERSION,

        "formation":
            FORMATION,

        "langues":
            LANGUES,

        "competences_confirmees":
            COMPETENCES_CONFIRMEES,

        "competences_protegees":
            COMPETENCES_PROTEGEES,

        "qualites_confirmees":
            QUALITES_CONFIRMEES,

        "intitules_cibles":
            INTITULES_CIBLES,

        "termes_contextuels":
            TERMES_CONTEXTUELS,

        "termes_non_confirmes":
            TERMES_NON_CONFIRMES
    }