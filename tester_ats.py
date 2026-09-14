import json
from pathlib import Path

from ai.analyzer import ANALYSE_VERSION
from core.ats_analyzer import analyser_ats
from core.database import connexion


DOSSIER_SORTIE = Path(
    "candidatures"
) / "ats_tests"


def recuperer_meilleure_offre():

    with connexion() as conn:

        ligne = conn.execute(
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
                o.score_final,
                o.statut,

                a.cv_recommande,
                a.resultat_json

            FROM offres AS o

            INNER JOIN analyses AS a
                ON a.offre_id = o.id

            WHERE
                a.analyse_version = ?
                AND a.cv_recommande IN (
                    'INGENIEUR',
                    'TECHNICIEN'
                )
                AND o.statut IN (
                    'PRIORITE_HAUTE',
                    'POSTULER'
                )

            ORDER BY
                o.score_final DESC,
                o.id DESC

            LIMIT 1
            """,
            (
                ANALYSE_VERSION,
            )
        ).fetchone()

    if ligne is None:
        raise RuntimeError(
            "Aucune offre compatible trouvée."
        )

    return ligne


def afficher_exigences(
    titre,
    exigences
):

    print()
    print(titre)
    print("-" * 70)

    if not exigences:

        print(
            "Aucune exigence détectée."
        )

        return

    symboles = {
        "CONFIRME": "✅",
        "PARTIEL": "⚠️",
        "ABSENT": "❌"
    }

    for exigence in exigences:

        statut = exigence.get(
            "statut",
            "ABSENT"
        )

        symbole = symboles.get(
            statut,
            "?"
        )

        terme = exigence.get(
            "terme",
            ""
        )

        preuve = exigence.get(
            "preuve",
            ""
        )

        print(
            f"{symbole} {terme}"
        )

        if preuve:

            print(
                f"   {preuve}"
            )


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


def main():

    print()
    print("=" * 78)
    print("TEST ATS SUR UNE VRAIE OFFRE")
    print("=" * 78)
    print()

    ligne = recuperer_meilleure_offre()

    offre = {
        "source":
            "SQLITE",

        "source_id":
            str(
                ligne["offre_id"]
            ),

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
            or ""
    }

    cv_recommande = (
        ligne["cv_recommande"]
        or ""
    )

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
        f"{ligne['score_final']}/100"
    )

    print(
        f"Décision : "
        f"{ligne['statut']}"
    )

    print(
        f"CV sélectionné : "
        f"{cv_recommande}"
    )

    print()
    print(
        "Analyse ATS avec GPT-OSS..."
    )

    analyse = analyser_ats(
        offre,
        cv_recommande
    )

    print()
    print("=" * 78)
    print("RESULTAT ATS")
    print("=" * 78)

    print(
        f"Pays : "
        f"{analyse['pays']}"
    )

    print(
        f"Pipeline : "
        f"{analyse['pipeline']}"
    )

    print(
        f"Langue annonce : "
        f"{analyse['langue_annonce']}"
    )

    print(
        f"Format CV recommandé : "
        f"{analyse['format_cv_recommande']}"
    )

    print()

    print(
        f"Score ATS contenu : "
        f"{analyse['score_ats_contenu']}/100"
    )

    print(
        f"Niveau ATS : "
        f"{analyse['niveau_ats']}"
    )

    print(
        f"Couverture obligatoire : "
        f"{analyse['couverture_obligatoire']}"
    )

    print(
        f"Couverture importante : "
        f"{analyse['couverture_importante']}"
    )

    print(
        f"Couverture bonus : "
        f"{analyse['couverture_bonus']}"
    )

    print(
        f"Obligatoires absents : "
        f"{analyse['nb_obligatoires_absents']}"
    )

    afficher_exigences(
        "EXIGENCES OBLIGATOIRES",
        analyse.get(
            "exigences_obligatoires",
            []
        )
    )

    afficher_exigences(
        "EXIGENCES IMPORTANTES",
        analyse.get(
            "exigences_importantes",
            []
        )
    )

    afficher_exigences(
        "CRITERES BONUS",
        analyse.get(
            "exigences_bonus",
            []
        )
    )

    afficher_liste(
        "MOTS-CLES ATS",
        analyse.get(
            "mots_cles_ats",
            []
        )
    )

    afficher_liste(
        "MOTS-CLES QUE LE CV PEUT INTEGRER HONNETEMENT",
        analyse.get(
            "mots_cles_a_integrer",
            []
        )
    )

    afficher_liste(
        "TERMES A NUANCER",
        analyse.get(
            "termes_a_nuancer",
            []
        )
    )

    afficher_liste(
        "MANQUES REELS",
        analyse.get(
            "manques_reels",
            []
        )
    )

    afficher_liste(
        "ADAPTATIONS RECOMMANDEES",
        analyse.get(
            "adaptations_cv",
            []
        )
    )

    afficher_liste(
        "RISQUES ATS",
        analyse.get(
            "risques_ats",
            []
        )
    )

    print()
    print("RESUME ATS")
    print("-" * 70)

    print(
        analyse.get(
            "resume_ats",
            ""
        )
    )

    # ========================================================
    # SAUVEGARDE LOCALE
    # ========================================================

    DOSSIER_SORTIE.mkdir(
        parents=True,
        exist_ok=True
    )

    chemin = (
        DOSSIER_SORTIE
        / f"ats_offre_{ligne['offre_id']}.json"
    )

    chemin.write_text(
        json.dumps(
            analyse,
            ensure_ascii=False,
            indent=2,
            default=str
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 78)

    print(
        f"Résultat sauvegardé : "
        f"{chemin}"
    )

    print(
        f"Temps ATS : "
        f"{analyse['temps_ats_secondes']} s"
    )

    print("=" * 78)
    print()


if __name__ == "__main__":
    main()