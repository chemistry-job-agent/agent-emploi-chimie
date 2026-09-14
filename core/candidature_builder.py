import json
import re
import shutil
import time

from datetime import datetime
from pathlib import Path

import ollama

from core.database import connexion
from core.cv_loader import charger_cvs


# ============================================================
# CONFIGURATION
# ============================================================

MODELE = "gpt-oss:20b"

DOSSIER_CANDIDATURES = Path(
    "candidatures"
)

PROFIL_PATH = Path(
    "profil.json"
)

DECISIONS_AUTORISEES = {
    "PRIORITE_HAUTE",
    "POSTULER"
}


# ============================================================
# OUTILS
# ============================================================

def nettoyer_nom_fichier(texte):
    texte = str(
        texte
        or ""
    ).strip()

    texte = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        texte
    )

    texte = re.sub(
        r"\s+",
        "_",
        texte
    )

    texte = re.sub(
        r"_+",
        "_",
        texte
    )

    return texte[
        :80
    ].strip(
        "_"
    )


def sauvegarder_json(
    chemin,
    donnees
):
    chemin.write_text(
        json.dumps(
            donnees,
            ensure_ascii=False,
            indent=2,
            default=str
        ),
        encoding="utf-8"
    )


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
# OFFRES ÉLIGIBLES
# ============================================================

def recuperer_offres_a_preparer():
    with connexion() as conn:

        lignes = conn.execute(
            """
            SELECT

                o.id AS offre_id,

                o.titre,
                o.entreprise,
                o.lieu,
                o.contrat,
                o.description,
                o.date_publication,
                o.experience,
                o.salaire,
                o.url_principale,

                o.score_prefiltre,
                o.score_ia,
                o.score_final,
                o.type_poste,
                o.cv_recommande,
                o.blocage_critique,
                o.statut,

                a.resultat_json,
                a.date_analyse

            FROM offres AS o

            INNER JOIN analyses AS a
                ON a.offre_id = o.id

            WHERE
                o.statut IN (
                    'PRIORITE_HAUTE',
                    'POSTULER'
                )

            ORDER BY
                o.score_final DESC,
                a.date_analyse DESC
            """
        ).fetchall()

    resultats = []

    for ligne in lignes:

        try:
            analyse = json.loads(
                ligne[
                    "resultat_json"
                ]
            )

        except Exception:
            continue

        resultats.append(
            {
                "offre_id":
                    ligne[
                        "offre_id"
                    ],

                "titre":
                    ligne[
                        "titre"
                    ]
                    or "",

                "entreprise":
                    ligne[
                        "entreprise"
                    ]
                    or "",

                "lieu":
                    ligne[
                        "lieu"
                    ]
                    or "",

                "contrat":
                    ligne[
                        "contrat"
                    ]
                    or "",

                "description":
                    ligne[
                        "description"
                    ]
                    or "",

                "date_publication":
                    ligne[
                        "date_publication"
                    ]
                    or "",

                "experience":
                    ligne[
                        "experience"
                    ]
                    or "",

                "salaire":
                    ligne[
                        "salaire"
                    ]
                    or "",

                "url":
                    ligne[
                        "url_principale"
                    ]
                    or "",

                "score_prefiltre":
                    ligne[
                        "score_prefiltre"
                    ],

                "score_ia":
                    ligne[
                        "score_ia"
                    ],

                "score_final":
                    ligne[
                        "score_final"
                    ],

                "type_poste":
                    ligne[
                        "type_poste"
                    ]
                    or "",

                "cv_recommande":
                    ligne[
                        "cv_recommande"
                    ]
                    or "AUCUN",

                "blocage_critique":
                    bool(
                        ligne[
                            "blocage_critique"
                        ]
                    ),

                "decision":
                    ligne[
                        "statut"
                    ]
                    or "",

                "analyse":
                    analyse,

                "date_analyse":
                    ligne[
                        "date_analyse"
                    ]
            }
        )

    return resultats


# ============================================================
# CANDIDATURE DÉJÀ PRÉPARÉE ?
# ============================================================

def candidature_existe(
    offre_id
):
    with connexion() as conn:

        ligne = conn.execute(
            """
            SELECT id

            FROM candidatures

            WHERE offre_id = ?

            LIMIT 1
            """,

            (
                offre_id,
            )
        ).fetchone()

    return (
        ligne is not None
    )


# ============================================================
# DOSSIER
# ============================================================

def creer_dossier_candidature(
    offre
):
    date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    entreprise = nettoyer_nom_fichier(
        offre.get(
            "entreprise",
            "Entreprise"
        )
    )

    titre = nettoyer_nom_fichier(
        offre.get(
            "titre",
            "Poste"
        )
    )

    offre_id = offre[
        "offre_id"
    ]

    nom = (
        f"{date}_"
        f"{offre_id}_"
        f"{entreprise}_"
        f"{titre}"
    )

    dossier = (
        DOSSIER_CANDIDATURES
        / nom
    )

    dossier.mkdir(
        parents=True,
        exist_ok=True
    )

    return dossier


# ============================================================
# CV
# ============================================================

def copier_cv_selectionne(
    offre,
    dossier
):
    cv_recommande = offre.get(
        "cv_recommande",
        "AUCUN"
    )

    if cv_recommande == "AUCUN":
        return ""

    cvs = charger_cvs()

    cv = cvs.get(
        cv_recommande
    )

    if not cv:
        return ""

    chemin_source = Path(
        cv.get(
            "chemin",
            ""
        )
    )

    if not chemin_source.exists():
        raise FileNotFoundError(
            f"CV introuvable : "
            f"{chemin_source}"
        )

    destination = (
        dossier
        / "CV_selectionne.pdf"
    )

    shutil.copy2(
        chemin_source,
        destination
    )

    return str(
        destination
    )


# ============================================================
# ADAPTATIONS CV
# ============================================================

def creer_adaptations_cv(
    offre,
    dossier
):
    analyse = offre[
        "analyse"
    ]

    adaptations = analyse.get(
        "adaptations_recommandees",
        []
    )

    points_forts = analyse.get(
        "points_forts_cv_choisi",
        []
    )

    faiblesses = analyse.get(
        "faiblesses_cv_choisi",
        []
    )

    lignes = []

    lignes.append(
        f"POSTE : "
        f"{offre['titre']}"
    )

    lignes.append(
        f"ENTREPRISE : "
        f"{offre['entreprise']}"
    )

    lignes.append(
        f"CV RECOMMANDÉ : "
        f"{offre['cv_recommande']}"
    )

    lignes.append(
        ""
    )

    lignes.append(
        "POINTS FORTS DU CV"
    )

    lignes.append(
        "=" * 60
    )

    if points_forts:

        for point in points_forts:
            lignes.append(
                f"- {point}"
            )

    else:
        lignes.append(
            "- Aucun point spécifique fourni."
        )

    lignes.append(
        ""
    )

    lignes.append(
        "FAIBLESSES DU CV"
    )

    lignes.append(
        "=" * 60
    )

    if faiblesses:

        for point in faiblesses:
            lignes.append(
                f"- {point}"
            )

    else:
        lignes.append(
            "- Aucune faiblesse spécifique fournie."
        )

    lignes.append(
        ""
    )

    lignes.append(
        "ADAPTATIONS RECOMMANDÉES"
    )

    lignes.append(
        "=" * 60
    )

    if adaptations:

        for adaptation in adaptations:
            lignes.append(
                f"- {adaptation}"
            )

    else:
        lignes.append(
            "- Aucune adaptation nécessaire."
        )

    chemin = (
        dossier
        / "adaptations_cv.txt"
    )

    chemin.write_text(
        "\n".join(
            lignes
        ),
        encoding="utf-8"
    )

    return chemin


# ============================================================
# LETTRE DE MOTIVATION
# ============================================================

def generer_lettre(
    offre
):
    profil = charger_profil()

    analyse = offre[
        "analyse"
    ]

    cvs = charger_cvs()

    cv_recommande = offre.get(
        "cv_recommande",
        "AUCUN"
    )

    cv = cvs.get(
        cv_recommande,
        {}
    )

    texte_cv = cv.get(
        "texte",
        ""
    )

    offre_json = json.dumps(
        {
            "titre":
                offre.get(
                    "titre",
                    ""
                ),

            "entreprise":
                offre.get(
                    "entreprise",
                    ""
                ),

            "lieu":
                offre.get(
                    "lieu",
                    ""
                ),

            "contrat":
                offre.get(
                    "contrat",
                    ""
                ),

            "description":
                offre.get(
                    "description",
                    ""
                ),

            "experience":
                offre.get(
                    "experience",
                    ""
                ),

            "salaire":
                offre.get(
                    "salaire",
                    ""
                ),

            "url":
                offre.get(
                    "url",
                    ""
                )
        },
        ensure_ascii=False,
        indent=2
    )

    analyse_json = json.dumps(
        {
            "compatibilite":
                analyse.get(
                    "compatibilite",
                    0
                ),

            "score_final":
                analyse.get(
                    "score_final",
                    0
                ),

            "forces":
                analyse.get(
                    "forces",
                    []
                ),

            "manques":
                analyse.get(
                    "manques",
                    []
                ),

            "exigences_obligatoires":
                analyse.get(
                    "exigences_obligatoires",
                    []
                ),

            "exigences_importantes":
                analyse.get(
                    "exigences_importantes",
                    []
                ),

            "adaptations_recommandees":
                analyse.get(
                    "adaptations_recommandees",
                    []
                )
        },
        ensure_ascii=False,
        indent=2
    )

    profil_json = json.dumps(
        profil,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
Tu rédiges une lettre de motivation professionnelle
en français pour une candidature à une offre d'emploi.

RÈGLE ABSOLUE :
N'invente aucune compétence, expérience, responsabilité,
certification ou durée d'expérience.

Toute information concernant le candidat doit être
justifiée par le profil ou le CV fourni.

Ne transforme jamais :
- une notion en maîtrise ;
- une interprétation de résultats en pratique autonome ;
- un stage en plusieurs années d'expérience industrielle.

La lettre doit être naturelle, crédible et personnalisée.

Elle doit tenir approximativement sur une page.

Évite :
- les formulations pompeuses ;
- les superlatifs artificiels ;
- les répétitions ;
- les phrases génériques sans lien avec l'offre.

Ne mentionne pas le score de compatibilité,
le score final ou le fonctionnement de l'IA.

Ne prétends pas connaître l'entreprise au-delà
des informations présentes dans l'offre.

Structure souhaitée :

1. Objet de candidature.
2. Introduction courte.
3. Expérience et compétences pertinentes.
4. Correspondance avec les missions.
5. Motivation pour le poste.
6. Conclusion et disponibilité.

============================================================
PROFIL
============================================================

{profil_json}

============================================================
CV SÉLECTIONNÉ
============================================================

{texte_cv}

============================================================
OFFRE
============================================================

{offre_json}

============================================================
ANALYSE DE CORRESPONDANCE
============================================================

{analyse_json}

============================================================
SORTIE
============================================================

Réponds uniquement avec la lettre finale en français.
"""

    debut = time.time()

    reponse = ollama.chat(
        model=MODELE,

        messages=[
            {
                "role":
                    "user",

                "content":
                    prompt
            }
        ],

        think="low",

        options={
            "temperature": 0.2,
            "num_ctx": 12288
        },

        keep_alive="30m"
    )

    lettre = (
        reponse[
            "message"
        ][
            "content"
        ]
        .strip()
    )

    return (
        lettre,
        round(
            time.time()
            - debut,
            1
        )
    )


# ============================================================
# ENREGISTREMENT CANDIDATURE SQLITE
# ============================================================

def enregistrer_candidature(
    offre_id,
    cv_utilise,
    dossier
):
    date = (
        datetime.now()
        .astimezone()
        .isoformat(
            timespec="seconds"
        )
    )

    notes = (
        f"Dossier préparé automatiquement : "
        f"{dossier}"
    )

    with connexion() as conn:

        ligne = conn.execute(
            """
            SELECT id

            FROM candidatures

            WHERE offre_id = ?

            LIMIT 1
            """,

            (
                offre_id,
            )
        ).fetchone()

        if ligne:

            conn.execute(
                """
                UPDATE candidatures

                SET
                    statut = 'PREPAREE',
                    cv_utilise = ?,
                    notes = ?,
                    date_modification = ?

                WHERE id = ?
                """,

                (
                    cv_utilise,
                    notes,
                    date,
                    ligne[
                        "id"
                    ]
                )
            )

        else:

            conn.execute(
                """
                INSERT INTO candidatures (

                    offre_id,
                    statut,
                    cv_utilise,
                    lettre_path,
                    notes,
                    date_creation,
                    date_modification

                )

                VALUES (
                    ?,
                    'PREPAREE',
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
                """,

                (
                    offre_id,

                    cv_utilise,

                    str(
                        dossier
                        / "lettre_motivation.txt"
                    ),

                    notes,

                    date,
                    date
                )
            )

        conn.commit()


# ============================================================
# PRÉPARATION D'UNE CANDIDATURE
# ============================================================

def preparer_candidature(
    offre,
    generer_lettre_ia=True
):
    if (
        offre.get(
            "decision"
        )
        not in DECISIONS_AUTORISEES
    ):
        return None

    if offre.get(
        "blocage_critique",
        False
    ):
        return None

    if (
        offre.get(
            "cv_recommande"
        )
        == "AUCUN"
    ):
        return None

    dossier = creer_dossier_candidature(
        offre
    )

    # --------------------------------------------------------
    # OFFRE
    # --------------------------------------------------------

    offre_export = {
        cle: valeur
        for cle, valeur
        in offre.items()
        if cle != "analyse"
    }

    sauvegarder_json(
        dossier
        / "offre.json",
        offre_export
    )

    # --------------------------------------------------------
    # ANALYSE
    # --------------------------------------------------------

    sauvegarder_json(
        dossier
        / "analyse.json",
        offre[
            "analyse"
        ]
    )

    # --------------------------------------------------------
    # CV
    # --------------------------------------------------------

    cv_copie = copier_cv_selectionne(
        offre,
        dossier
    )

    # --------------------------------------------------------
    # ADAPTATIONS
    # --------------------------------------------------------

    creer_adaptations_cv(
        offre,
        dossier
    )

    # --------------------------------------------------------
    # LETTRE
    # --------------------------------------------------------

    temps_lettre = 0

    if generer_lettre_ia:

        lettre, temps_lettre = (
            generer_lettre(
                offre
            )
        )

        (
            dossier
            / "lettre_motivation.txt"
        ).write_text(
            lettre,
            encoding="utf-8"
        )

    else:

        (
            dossier
            / "lettre_motivation.txt"
        ).write_text(
            "Lettre non générée.",
            encoding="utf-8"
        )

    # --------------------------------------------------------
    # MÉTADONNÉES
    # --------------------------------------------------------

    metadata = {
        "offre_id":
            offre[
                "offre_id"
            ],

        "titre":
            offre[
                "titre"
            ],

        "entreprise":
            offre[
                "entreprise"
            ],

        "decision_agent":
            offre[
                "decision"
            ],

        "score_final":
            offre.get(
                "score_final",
                0
            ),

        "cv_recommande":
            offre[
                "cv_recommande"
            ],

        "cv_copie":
            cv_copie,

        "lettre_generee":
            generer_lettre_ia,

        "temps_lettre_secondes":
            temps_lettre,

        "statut_candidature":
            "PREPAREE",

        "validation_humaine_requise":
            True,

        "envoyee":
            False
    }

    sauvegarder_json(
        dossier
        / "candidature.json",
        metadata
    )

    enregistrer_candidature(
        offre_id=
            offre[
                "offre_id"
            ],

        cv_utilise=
            cv_copie,

        dossier=
            dossier
    )

    return {
        "dossier":
            str(
                dossier
            ),

        "metadata":
            metadata
    }