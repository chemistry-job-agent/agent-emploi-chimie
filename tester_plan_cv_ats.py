import json
import re

from pathlib import Path

from core.cv_ats_plan import (
    construire_plan_cv
)

from core.database import connexion


DOSSIER_ATS = (
    Path("candidatures")
    / "ats_tests"
)


# ============================================================
# TROUVER LE DERNIER ATS SECURISE
# ============================================================

def trouver_dernier_ats_securise():

    fichiers = list(
        DOSSIER_ATS.glob(
            "ats_offre_*_securise.json"
        )
    )

    if not fichiers:
        raise FileNotFoundError(
            "Aucun fichier ATS sécurisé trouvé."
        )

    return max(
        fichiers,
        key=lambda fichier:
            fichier.stat().st_mtime
    )


# ============================================================
# EXTRAIRE ID OFFRE
# ============================================================

def extraire_offre_id(
    fichier
):

    correspondance = re.search(
        r"ats_offre_(\d+)_securise\.json$",
        fichier.name
    )

    if not correspondance:

        raise ValueError(
            "Impossible de déterminer "
            "l'identifiant de l'offre."
        )

    return int(
        correspondance.group(
            1
        )
    )


# ============================================================
# CHARGER OFFRE SQLITE
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
                date_publication,
                experience,
                salaire,
                url_principale,
                score_final,
                statut,
                cv_recommande

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

        "date_publication":
            ligne["date_publication"]
            or "",

        "experience":
            ligne["experience"]
            or "",

        "salaire":
            ligne["salaire"]
            or "",

        "url":
            ligne["url_principale"]
            or "",

        "score_final":
            ligne["score_final"],

        "statut":
            ligne["statut"]
            or "",

        "cv_recommande":
            ligne["cv_recommande"]
            or ""
    }


# ============================================================
# AFFICHAGE
# ============================================================

def afficher_liste(
    titre,
    elements
):

    print()
    print(titre)
    print("-" * 70)

    if not elements:

        print(
            "Aucun."
        )

        return

    for element in elements:

        print(
            f"- {element}"
        )


# ============================================================
# PROGRAMME
# ============================================================

def main():

    print()
    print("=" * 78)

    print(
        "CONSTRUCTION DU PLAN CV ATS SECURISE"
    )

    print("=" * 78)

    fichier_ats = (
        trouver_dernier_ats_securise()
    )

    offre_id = extraire_offre_id(
        fichier_ats
    )

    analyse_ats = json.loads(
        fichier_ats.read_text(
            encoding="utf-8"
        )
    )

    offre = charger_offre(
        offre_id
    )

    cv_source = (
        analyse_ats.get(
            "cv_source"
        )
        or offre.get(
            "cv_recommande"
        )
        or "TECHNICIEN"
    )

    plan = construire_plan_cv(
        offre=offre,
        analyse_ats=analyse_ats,
        cv_source=cv_source
    )

    # ========================================================
    # AFFICHAGE GENERAL
    # ========================================================

    print()

    print(
        f"Offre : "
        f"{offre['titre']}"
    )

    print(
        f"Entreprise : "
        f"{offre['entreprise']}"
    )

    print(
        f"Lieu : "
        f"{offre['lieu']}"
    )

    print(
        f"Score actuel : "
        f"{offre['score_final']}/100"
    )

    print(
        f"Décision : "
        f"{offre['statut']}"
    )

    print()

    print(
        f"CV source : "
        f"{plan['cv_source']}"
    )

    print(
        f"Titre CV : "
        f"{plan['titre_cv']}"
    )

    print(
        f"Pays : "
        f"{plan['pays']}"
    )

    print(
        f"Langue : "
        f"{plan['langue']}"
    )

    print(
        f"Format : "
        f"{plan['format_cv']}"
    )

    # ========================================================
    # CONTENU
    # ========================================================

    afficher_liste(
        "COMPETENCES CONFIRMEES AUTORISEES",
        plan.get(
            "competences_confirmees",
            []
        )
    )

    afficher_liste(
        "COMPETENCES A NIVEAU PROTEGE",
        plan.get(
            "competences_niveau_protege",
            []
        )
    )

    afficher_liste(
        "QUALITES CONFIRMEES",
        plan.get(
            "qualites_confirmees",
            []
        )
    )

    afficher_liste(
        "VALIDATION HUMAINE NECESSAIRE",
        plan.get(
            "validation_humaine",
            []
        )
    )

    afficher_liste(
        "INTERDITS",
        plan.get(
            "interdits",
            []
        )
    )

    afficher_liste(
        "TERMES INCONNUS",
        plan.get(
            "inconnus",
            []
        )
    )

    afficher_liste(
        "MISSIONS FUTURES DE L'OFFRE",
        plan.get(
            "missions_futures",
            []
        )
    )

    afficher_liste(
        "FORMATIONS POSSIBLES APRES EMBAUCHE",
        plan.get(
            "formations_possibles",
            []
        )
    )

    afficher_liste(
        "REGLES DE GENERATION",
        plan.get(
            "regles_generation",
            []
        )
    )

    # ========================================================
    # SAUVEGARDE
    # ========================================================

    destination = (
        DOSSIER_ATS
        / f"plan_cv_offre_{offre_id}.json"
    )

    destination.write_text(
        json.dumps(
            plan,
            ensure_ascii=False,
            indent=2,
            default=str
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 78)

    print(
        f"Plan sauvegardé : "
        f"{destination}"
    )

    print(
        "Aucun appel GPT-OSS effectué."
    )

    print(
        "Aucun CV n'a encore été modifié."
    )

    print("=" * 78)
    print()


if __name__ == "__main__":
    main()