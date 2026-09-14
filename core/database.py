import hashlib
import json
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = Path(
    "agent_emploi_v2.db"
)

ANALYSE_VERSION_PAR_DEFAUT = "fullcv_v1"


# ============================================================
# CONNEXION
# ============================================================

def connexion():
    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# OUTILS
# ============================================================

def maintenant():
    return (
        datetime.now()
        .astimezone()
        .isoformat(
            timespec="seconds"
        )
    )


def normaliser_texte(texte):
    if texte is None:
        return ""

    texte = str(
        texte
    ).strip().lower()

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

    texte = " ".join(
        texte.split()
    )

    return texte


def creer_fingerprint(offre):
    titre = normaliser_texte(
        offre.get(
            "titre",
            ""
        )
    )

    entreprise = normaliser_texte(
        offre.get(
            "entreprise",
            ""
        )
    )

    lieu = normaliser_texte(
        offre.get(
            "lieu",
            ""
        )
    )

    texte = (
        f"{titre}|"
        f"{entreprise}|"
        f"{lieu}"
    )

    return hashlib.sha256(
        texte.encode(
            "utf-8"
        )
    ).hexdigest()


def json_securise(objet):
    return json.dumps(
        objet,
        ensure_ascii=False,
        default=str
    )


# ============================================================
# INITIALISATION DE LA BASE
# ============================================================

def initialiser_base():
    with connexion() as conn:

        # ----------------------------------------------------
        # OFFRES
        # ----------------------------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS offres (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                fingerprint TEXT
                    NOT NULL
                    UNIQUE,

                titre TEXT,

                entreprise TEXT,

                lieu TEXT,

                contrat TEXT,

                description TEXT,

                date_publication TEXT,

                experience TEXT,

                salaire TEXT,

                url_principale TEXT,

                statut TEXT
                    NOT NULL
                    DEFAULT 'NOUVELLE',

                score_prefiltre INTEGER,

                score_ia INTEGER,

                score_final INTEGER,

                type_poste TEXT,

                cv_recommande TEXT,

                blocage_critique INTEGER
                    DEFAULT 0,

                resume_ia TEXT,

                date_premiere_vue TEXT
                    NOT NULL,

                date_derniere_vue TEXT
                    NOT NULL
            )
        """)

        # ----------------------------------------------------
        # SOURCES D'UNE OFFRE
        # ----------------------------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS offre_sources (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                offre_id INTEGER
                    NOT NULL,

                source TEXT
                    NOT NULL,

                source_id TEXT
                    NOT NULL,

                url TEXT,

                donnees_brutes TEXT,

                date_detection TEXT
                    NOT NULL,

                UNIQUE(
                    source,
                    source_id
                ),

                FOREIGN KEY(
                    offre_id
                )
                REFERENCES offres(id)
                ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # ANALYSES GPT-OSS
        # ----------------------------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                offre_id INTEGER
                    NOT NULL,

                analyse_version TEXT
                    NOT NULL,

                modele TEXT,

                compatibilite INTEGER,

                score_cv_ingenieur INTEGER,

                score_cv_technicien INTEGER,

                cv_recommande TEXT,

                fichier_cv TEXT,

                blocage_critique INTEGER
                    DEFAULT 0,

                temps_ia_secondes REAL,

                resultat_json TEXT
                    NOT NULL,

                date_analyse TEXT
                    NOT NULL,

                UNIQUE(
                    offre_id,
                    analyse_version
                ),

                FOREIGN KEY(
                    offre_id
                )
                REFERENCES offres(id)
                ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # CANDIDATURES
        # ----------------------------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidatures (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                offre_id INTEGER
                    NOT NULL,

                statut TEXT
                    NOT NULL
                    DEFAULT 'A_PREPARER',

                cv_utilise TEXT,

                lettre_path TEXT,

                notes TEXT,

                date_creation TEXT
                    NOT NULL,

                date_modification TEXT
                    NOT NULL,

                FOREIGN KEY(
                    offre_id
                )
                REFERENCES offres(id)
                ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # FEEDBACK
        # ----------------------------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                offre_id INTEGER,

                decision TEXT,

                commentaire TEXT,

                date_feedback TEXT
                    NOT NULL,

                FOREIGN KEY(
                    offre_id
                )
                REFERENCES offres(id)
                ON DELETE SET NULL
            )
        """)

        # ----------------------------------------------------
        # INDEX
        # ----------------------------------------------------

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_offres_statut

            ON offres(
                statut
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_offres_score_ia

            ON offres(
                score_ia
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_analyses_offre

            ON analyses(
                offre_id
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_analyses_version

            ON analyses(
                analyse_version
            )
        """)

        conn.commit()


# ============================================================
# SOURCE
# ============================================================

def enregistrer_source(
    conn,
    offre_id,
    offre
):
    source = str(
        offre.get(
            "source",
            "INCONNUE"
        )
        or "INCONNUE"
    )

    source_id = str(
        offre.get(
            "source_id",
            ""
        )
        or ""
    ).strip()

    url = str(
        offre.get(
            "url",
            ""
        )
        or ""
    ).strip()

    # Certaines sources peuvent ne pas fournir d'identifiant.
    # On crée alors un identifiant stable à partir de l'URL.
    if not source_id:

        if url:
            source_id = hashlib.sha256(
                url.encode(
                    "utf-8"
                )
            ).hexdigest()

        else:
            source_id = (
                f"offre-{offre_id}-"
                f"{normaliser_texte(source)}"
            )

    donnees_brutes = offre.get(
        "donnees_brutes",
        offre
    )

    conn.execute(
        """
        INSERT INTO offre_sources (

            offre_id,
            source,
            source_id,
            url,
            donnees_brutes,
            date_detection

        )

        VALUES (
            ?, ?, ?, ?, ?, ?
        )

        ON CONFLICT(
            source,
            source_id
        )

        DO UPDATE SET

            offre_id =
                excluded.offre_id,

            url =
                excluded.url,

            donnees_brutes =
                excluded.donnees_brutes
        """,

        (
            offre_id,
            source,
            source_id,
            url,
            json_securise(
                donnees_brutes
            ),
            maintenant()
        )
    )


# ============================================================
# ENREGISTREMENT D'UNE OFFRE
# ============================================================

def _enregistrer_offre_conn(
    conn,
    offre
):
    fingerprint = creer_fingerprint(
        offre
    )

    date_actuelle = maintenant()

    ligne = conn.execute(
        """
        SELECT id
        FROM offres
        WHERE fingerprint = ?
        """,
        (
            fingerprint,
        )
    ).fetchone()

    # --------------------------------------------------------
    # OFFRE DÉJÀ CONNUE
    # --------------------------------------------------------

    if ligne:
        offre_id = ligne[
            "id"
        ]

        conn.execute(
            """
            UPDATE offres

            SET
                titre = ?,
                entreprise = ?,
                lieu = ?,
                contrat = ?,
                description = ?,
                date_publication = ?,
                experience = ?,
                salaire = ?,
                url_principale = ?,
                date_derniere_vue = ?

            WHERE id = ?
            """,

            (
                offre.get(
                    "titre",
                    ""
                ),

                offre.get(
                    "entreprise",
                    ""
                ),

                offre.get(
                    "lieu",
                    ""
                ),

                offre.get(
                    "contrat",
                    ""
                ),

                offre.get(
                    "description",
                    ""
                ),

                offre.get(
                    "date_publication",
                    ""
                ),

                offre.get(
                    "experience",
                    ""
                ),

                offre.get(
                    "salaire",
                    ""
                ),

                offre.get(
                    "url",
                    ""
                ),

                date_actuelle,

                offre_id
            )
        )

        est_nouvelle = False

    # --------------------------------------------------------
    # NOUVELLE OFFRE
    # --------------------------------------------------------

    else:
        curseur = conn.execute(
            """
            INSERT INTO offres (

                fingerprint,

                titre,
                entreprise,
                lieu,
                contrat,
                description,

                date_publication,
                experience,
                salaire,

                url_principale,

                statut,

                date_premiere_vue,
                date_derniere_vue

            )

            VALUES (
                ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?,
                'NOUVELLE',
                ?, ?
            )
            """,

            (
                fingerprint,

                offre.get(
                    "titre",
                    ""
                ),

                offre.get(
                    "entreprise",
                    ""
                ),

                offre.get(
                    "lieu",
                    ""
                ),

                offre.get(
                    "contrat",
                    ""
                ),

                offre.get(
                    "description",
                    ""
                ),

                offre.get(
                    "date_publication",
                    ""
                ),

                offre.get(
                    "experience",
                    ""
                ),

                offre.get(
                    "salaire",
                    ""
                ),

                offre.get(
                    "url",
                    ""
                ),

                date_actuelle,
                date_actuelle
            )
        )

        offre_id = (
            curseur.lastrowid
        )

        est_nouvelle = True

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    enregistrer_source(
        conn,
        offre_id,
        offre
    )

    # Important :
    # main.py récupère cet identifiant directement
    # dans le dictionnaire de l'offre.
    offre[
        "_db_id"
    ] = offre_id

    return (
        offre_id,
        est_nouvelle
    )


def enregistrer_offre(
    offre
):
    with connexion() as conn:

        resultat = (
            _enregistrer_offre_conn(
                conn,
                offre
            )
        )

        conn.commit()

        return resultat


# ============================================================
# ENREGISTREMENT EN MASSE
# ============================================================

def enregistrer_liste_offres(
    offres
):
    nouvelles = 0

    deja_connues = 0

    with connexion() as conn:

        for offre in offres:

            _, est_nouvelle = (
                _enregistrer_offre_conn(
                    conn,
                    offre
                )
            )

            if est_nouvelle:
                nouvelles += 1

            else:
                deja_connues += 1

        conn.commit()

    return {
        "nouvelles": nouvelles,
        "deja_connues": deja_connues,
        "total_recu": len(
            offres
        )
    }


# ============================================================
# OFFRE DÉJÀ ANALYSÉE ?
# ============================================================

def offre_deja_analysee(
    offre_id,
    analyse_version=
        ANALYSE_VERSION_PAR_DEFAUT
):
    if not offre_id:
        return False

    with connexion() as conn:

        ligne = conn.execute(
            """
            SELECT id

            FROM analyses

            WHERE
                offre_id = ?
                AND analyse_version = ?

            LIMIT 1
            """,

            (
                offre_id,
                analyse_version
            )
        ).fetchone()

    return (
        ligne is not None
    )


# ============================================================
# ENREGISTREMENT D'UNE ANALYSE GPT-OSS
# ============================================================

def enregistrer_analyse(
    offre_id,
    analyse,
    score_prefiltre=0,
    analyse_version=ANALYSE_VERSION_PAR_DEFAUT
):
    if not offre_id:
        raise ValueError(
            "Impossible d'enregistrer "
            "l'analyse sans offre_id."
        )

    date_actuelle = maintenant()

    resultat_json = json_securise(
        analyse
    )

    modele = analyse.get(
        "modele",
        ""
    )

    compatibilite = int(
        analyse.get(
            "compatibilite",
            0
        )
        or 0
    )

    score_cv_ingenieur = int(
        analyse.get(
            "score_cv_ingenieur",
            0
        )
        or 0
    )

    score_cv_technicien = int(
        analyse.get(
            "score_cv_technicien",
            0
        )
        or 0
    )

    cv_recommande = analyse.get(
        "cv_recommande",
        "AUCUN"
    )

    fichier_cv = analyse.get(
        "fichier_cv",
        ""
    )

    blocage_critique = (
        1
        if analyse.get(
            "blocage_critique",
            False
        )
        else 0
    )

    temps_ia_secondes = analyse.get(
        "temps_ia_secondes"
    )

    score_final = int(
        analyse.get(
            "score_final",
            compatibilite
        )
        or compatibilite
    )

    decision = analyse.get(
        "decision",
        "ANALYSEE"
    )

    with connexion() as conn:

        # ====================================================
        # ANALYSE COMPLÈTE
        # ====================================================

        conn.execute(
            """
            INSERT INTO analyses (

                offre_id,
                analyse_version,
                modele,

                compatibilite,

                score_cv_ingenieur,
                score_cv_technicien,

                cv_recommande,
                fichier_cv,

                blocage_critique,

                temps_ia_secondes,

                resultat_json,
                date_analyse

            )

            VALUES (
                ?, ?, ?,
                ?,
                ?, ?,
                ?, ?,
                ?,
                ?,
                ?, ?
            )

            ON CONFLICT(
                offre_id,
                analyse_version
            )

            DO UPDATE SET

                modele =
                    excluded.modele,

                compatibilite =
                    excluded.compatibilite,

                score_cv_ingenieur =
                    excluded.score_cv_ingenieur,

                score_cv_technicien =
                    excluded.score_cv_technicien,

                cv_recommande =
                    excluded.cv_recommande,

                fichier_cv =
                    excluded.fichier_cv,

                blocage_critique =
                    excluded.blocage_critique,

                temps_ia_secondes =
                    excluded.temps_ia_secondes,

                resultat_json =
                    excluded.resultat_json,

                date_analyse =
                    excluded.date_analyse
            """,

            (
                offre_id,
                analyse_version,
                modele,

                compatibilite,

                score_cv_ingenieur,
                score_cv_technicien,

                cv_recommande,
                fichier_cv,

                blocage_critique,

                temps_ia_secondes,

                resultat_json,
                date_actuelle
            )
        )

        # ====================================================
        # RÉSUMÉ DANS LA TABLE OFFRES
        # ====================================================

        conn.execute(
            """
            UPDATE offres

            SET
                statut = ?,
                score_prefiltre = ?,
                score_ia = ?,
                score_final = ?,
                type_poste = ?,
                cv_recommande = ?,
                blocage_critique = ?,
                resume_ia = ?

            WHERE id = ?
            """,

            (
                decision,

                int(
                    score_prefiltre
                    or 0
                ),

                compatibilite,

                score_final,

                analyse.get(
                    "type_poste",
                    "AUTRE"
                ),

                cv_recommande,

                blocage_critique,

                analyse.get(
                    "resume",
                    ""
                ),

                offre_id
            )
        )

        conn.commit()

# ============================================================
# CHARGEMENT D'UNE ANALYSE
# ============================================================

def charger_analyse(
    offre_id,
    analyse_version=
        ANALYSE_VERSION_PAR_DEFAUT
):
    with connexion() as conn:

        ligne = conn.execute(
            """
            SELECT resultat_json

            FROM analyses

            WHERE
                offre_id = ?
                AND analyse_version = ?

            LIMIT 1
            """,

            (
                offre_id,
                analyse_version
            )
        ).fetchone()

    if not ligne:
        return None

    try:
        return json.loads(
            ligne[
                "resultat_json"
            ]
        )

    except Exception:
        return None


# ============================================================
# RÉCUPÉRER TOUTES LES ANALYSES
# ============================================================

def recuperer_analyses(
    analyse_version=
        ANALYSE_VERSION_PAR_DEFAUT
):
    with connexion() as conn:

        lignes = conn.execute(
            """
            SELECT

                o.id AS offre_id,

                o.titre,
                o.entreprise,
                o.lieu,
                o.contrat,
                o.date_publication,
                o.experience,
                o.salaire,
                o.url_principale,

                o.score_prefiltre,

                a.resultat_json,
                a.date_analyse

            FROM analyses AS a

            INNER JOIN offres AS o
                ON o.id = a.offre_id

            WHERE
                a.analyse_version = ?

            ORDER BY
                a.compatibilite DESC,
                a.date_analyse DESC
            """,

            (
                analyse_version,
            )
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

        resultat = {
            "db_id":
                ligne[
                    "offre_id"
                ],

            "titre":
                ligne[
                    "titre"
                ],

            "entreprise":
                ligne[
                    "entreprise"
                ],

            "lieu":
                ligne[
                    "lieu"
                ],

            "contrat":
                ligne[
                    "contrat"
                ],

            "date_publication":
                ligne[
                    "date_publication"
                ],

            "experience":
                ligne[
                    "experience"
                ],

            "salaire":
                ligne[
                    "salaire"
                ],

            "url":
                ligne[
                    "url_principale"
                ],

            "score_prefiltre":
                ligne[
                    "score_prefiltre"
                ],

            "date_analyse":
                ligne[
                    "date_analyse"
                ]
        }

        resultat.update(
            analyse
        )

        resultats.append(
            resultat
        )

    return resultats


# ============================================================
# STATISTIQUES
# ============================================================

def compter_offres():
    with connexion() as conn:

        ligne = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM offres
            """
        ).fetchone()

    return int(
        ligne[
            "total"
        ]
    )


def compter_sources():
    with connexion() as conn:

        lignes = conn.execute(
            """
            SELECT
                source,
                COUNT(*) AS total

            FROM offre_sources

            GROUP BY source

            ORDER BY total DESC
            """
        ).fetchall()

    return {
        ligne[
            "source"
        ]: int(
            ligne[
                "total"
            ]
        )

        for ligne in lignes
    }


def compter_analyses(
    analyse_version=
        ANALYSE_VERSION_PAR_DEFAUT
):
    with connexion() as conn:

        ligne = conn.execute(
            """
            SELECT COUNT(*) AS total

            FROM analyses

            WHERE analyse_version = ?
            """,

            (
                analyse_version,
            )
        ).fetchone()

    return int(
        ligne[
            "total"
        ]
    )