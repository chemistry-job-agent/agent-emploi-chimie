import json
from pathlib import Path

from core.database import (
    connexion,
    initialiser_base
)


DOSSIER_CANDIDATURES = Path(
    "candidatures"
)


# ============================================================
# COLONNES ATTENDUES
# ============================================================

COLONNES_ATTENDUES = {
    "statut":
        "TEXT DEFAULT 'A_PREPARER'",

    "cv_utilise":
        "TEXT",

    "lettre_path":
        "TEXT",

    "notes":
        "TEXT",

    "date_creation":
        "TEXT",

    "date_modification":
        "TEXT"
}


# ============================================================
# MIGRATION DE LA TABLE
# ============================================================

def migrer_table():
    initialiser_base()

    with connexion() as conn:

        lignes = conn.execute(
            """
            PRAGMA table_info(candidatures)
            """
        ).fetchall()

        colonnes_existantes = {
            ligne["name"]
            for ligne in lignes
        }

        print()
        print("=" * 70)
        print("VÉRIFICATION TABLE CANDIDATURES")
        print("=" * 70)

        for nom, type_sql in (
            COLONNES_ATTENDUES.items()
        ):

            if nom in colonnes_existantes:

                print(
                    f"✅ {nom}"
                )

                continue

            print(
                f"➕ Ajout colonne : {nom}"
            )

            conn.execute(
                f"""
                ALTER TABLE candidatures
                ADD COLUMN {nom} {type_sql}
                """
            )

        conn.commit()


# ============================================================
# RÉCUPÉRATION DES DOSSIERS DÉJÀ CRÉÉS
# ============================================================

def reparer_dossiers_existants():

    if not DOSSIER_CANDIDATURES.exists():

        print()
        print(
            "Aucun dossier candidatures."
        )

        return

    fichiers = list(
        DOSSIER_CANDIDATURES.glob(
            "*/candidature.json"
        )
    )

    print()
    print("=" * 70)
    print("RÉCUPÉRATION DES CANDIDATURES DÉJÀ GÉNÉRÉES")
    print("=" * 70)

    print(
        f"Dossiers trouvés : {len(fichiers)}"
    )

    reparees = 0
    deja_presentes = 0
    erreurs = 0

    for fichier in fichiers:

        dossier = fichier.parent

        try:

            metadata = json.loads(
                fichier.read_text(
                    encoding="utf-8"
                )
            )

            offre_id = metadata.get(
                "offre_id"
            )

            if not offre_id:

                print(
                    f"⚠️ Offre ID absente : "
                    f"{dossier.name}"
                )

                erreurs += 1

                continue

            cv_utilise = metadata.get(
                "cv_copie",
                ""
            )

            lettre_path = str(
                dossier
                / "lettre_motivation.txt"
            )

            notes = (
                "Dossier préparé automatiquement : "
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

                    deja_presentes += 1

                    print(
                        f"♻️ Déjà présente : "
                        f"{dossier.name}"
                    )

                    continue

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
                        datetime('now'),
                        datetime('now')
                    )
                    """,
                    (
                        offre_id,
                        cv_utilise,
                        lettre_path,
                        notes
                    )
                )

                conn.commit()

            reparees += 1

            print(
                f"✅ Récupérée : "
                f"{dossier.name}"
            )

        except Exception as erreur:

            erreurs += 1

            print(
                f"❌ {dossier.name} : "
                f"{erreur}"
            )

    print()
    print("=" * 70)
    print("BILAN")
    print("=" * 70)

    print(
        f"✅ Récupérées : {reparees}"
    )

    print(
        f"♻️ Déjà présentes : "
        f"{deja_presentes}"
    )

    print(
        f"❌ Erreurs : {erreurs}"
    )

    print()


# ============================================================
# PROGRAMME
# ============================================================

def main():

    migrer_table()

    reparer_dossiers_existants()


if __name__ == "__main__":

    main()