import json
import re

from pathlib import Path

from core.cv_ats_generator import (
    construire_brouillon_cv,
    sauvegarder_brouillon
)

from core.database import connexion


DOSSIER_ATS = (
    Path("candidatures")
    / "ats_tests"
)


# ============================================================
# PLAN LE PLUS RECENT
# ============================================================

def trouver_dernier_plan():

    fichiers = list(
        DOSSIER_ATS.glob(
            "plan_cv_offre_*.json"
        )
    )

    if not fichiers:

        raise FileNotFoundError(
            "Aucun plan CV ATS trouvé."
        )

    return max(
        fichiers,
        key=lambda fichier:
            fichier.stat().st_mtime
    )


# ============================================================
# ID OFFRE
# ============================================================

def extraire_offre_id(
    fichier
):

    correspondance = re.search(
        r"plan_cv_offre_(\d+)\.json$",
        fichier.name
    )

    if not correspondance:

        raise ValueError(
            "ID offre impossible à déterminer."
        )

    return int(
        correspondance.group(
            1
        )
    )


# ============================================================
# OFFRE
# ============================================================

def charger_offre(
    offre_id
):

    with connexion() as conn:

        ligne = conn.execute(
            """
            SELECT
                id,
                titre,
                entreprise,
                lieu,
                contrat,
                description,
                experience,
                salaire,
                url_principale

            FROM offres

            WHERE id = ?

            LIMIT 1
            """,
            (
                offre_id,
            )
        ).fetchone()

    if ligne is None:

        raise RuntimeError(
            f"Offre {offre_id} introuvable."
        )

    return {
        "id":
            ligne["id"],

        "titre":
            ligne["titre"]
            or "",

        "entreprise":
            ligne["entreprise"]
            or "",

        "lieu":
            ligne["lieu"]
            or "",

        "contrat":
            ligne["contrat"]
            or "",

        "description":
            ligne["description"]
            or "",

        "experience":
            ligne["experience"]
            or "",

        "salaire":
            ligne["salaire"]
            or "",

        "url":
            ligne["url_principale"]
            or ""
    }


# ============================================================
# PROGRAMME
# ============================================================

def main():

    print()
    print("=" * 78)
    print("GENERATION BROUILLON CV ATS SECURISE")
    print("=" * 78)

    fichier_plan = trouver_dernier_plan()

    plan = json.loads(
        fichier_plan.read_text(
            encoding="utf-8"
        )
    )

    offre_id = extraire_offre_id(
        fichier_plan
    )

    offre = charger_offre(
        offre_id
    )

    print()
    print(
        f"Offre : {offre['titre']}"
    )

    print(
        f"Entreprise : {offre['entreprise']}"
    )

    print(
        f"CV source : {plan['cv_source']}"
    )

    print(
        f"Titre cible : {plan['titre_cv']}"
    )

    print()

    brouillon = construire_brouillon_cv(
        offre,
        plan
    )

    fichiers = sauvegarder_brouillon(
        brouillon,
        DOSSIER_ATS
    )

    print(
        "✅ Brouillon sécurisé généré."
    )

    print()

    print(
        f"JSON : {fichiers['json']}"
    )

    print(
        f"TXT  : {fichiers['txt']}"
    )

    print()

    print(
        "🔒 Garde-fou anti-invention : actif"
    )

    print(
        "🧠 Aucun appel GPT-OSS effectué"
    )

    print(
        "📄 Le CV PDF original n'a pas été modifié"
    )

    print(
        "👤 Validation humaine toujours requise"
    )

    print()
    print("=" * 78)


if __name__ == "__main__":
    main()