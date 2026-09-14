import json

from core.database import (
    connexion,
    initialiser_base
)

from core.scorer import (
    calculer_score_final
)

from ai.analyzer import (
    ANALYSE_VERSION
)


def charger_analyses():
    with connexion() as conn:

        lignes = conn.execute(
            """
            SELECT

                a.id AS analyse_id,
                a.offre_id,
                a.resultat_json,

                o.titre,
                o.entreprise,
                o.lieu,
                o.contrat,
                o.description,
                o.date_publication,
                o.experience,
                o.salaire,
                o.url_principale,
                o.score_prefiltre

            FROM analyses AS a

            INNER JOIN offres AS o
                ON o.id = a.offre_id

            WHERE
                a.analyse_version = ?

            ORDER BY a.id ASC
            """,

            (
                ANALYSE_VERSION,
            )
        ).fetchall()

    return lignes


def construire_offre(ligne):
    return {
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


def migrer():
    initialiser_base()

    lignes = charger_analyses()

    print()
    print("=" * 72)
    print("MIGRATION DES SCORES")
    print("=" * 72)

    print(
        f"Version d'analyse : "
        f"{ANALYSE_VERSION}"
    )

    print(
        f"Analyses trouvées : "
        f"{len(lignes)}"
    )

    print()

    migrees = 0
    deja_ok = 0
    erreurs = 0

    for numero, ligne in enumerate(
        lignes,
        start=1
    ):
        try:
            analyse = json.loads(
                ligne[
                    "resultat_json"
                ]
            )

        except Exception as erreur:
            erreurs += 1

            print(
                f"❌ [{numero}] "
                f"JSON illisible : "
                f"{erreur}"
            )

            continue

        # ----------------------------------------------------
        # SI LE SCORE EXISTE DÉJÀ
        # ----------------------------------------------------

        if (
            "score_final" in analyse
            and
            "decision" in analyse
        ):
            deja_ok += 1

            print(
                f"♻️ [{numero}] Déjà migrée - "
                f"{ligne['titre']}"
            )

            continue

        # ----------------------------------------------------
        # RECONSTRUCTION DE L'OFFRE
        # ----------------------------------------------------

        offre = construire_offre(
            ligne
        )

        # ----------------------------------------------------
        # CALCUL DU SCORE
        # ----------------------------------------------------

        score = calculer_score_final(
            offre,
            analyse
        )

        analyse.update(
            score
        )

        resultat_json = json.dumps(
            analyse,
            ensure_ascii=False,
            default=str
        )

        # ----------------------------------------------------
        # MISE À JOUR SQLITE
        # ----------------------------------------------------

        with connexion() as conn:

            conn.execute(
                """
                UPDATE analyses

                SET resultat_json = ?

                WHERE id = ?
                """,

                (
                    resultat_json,
                    ligne[
                        "analyse_id"
                    ]
                )
            )

            conn.execute(
                """
                UPDATE offres

                SET
                    score_final = ?,
                    statut = ?

                WHERE id = ?
                """,

                (
                    analyse[
                        "score_final"
                    ],

                    analyse[
                        "decision"
                    ],

                    ligne[
                        "offre_id"
                    ]
                )
            )

            conn.commit()

        migrees += 1

        print(
            f"✅ [{numero}] "
            f"{ligne['titre']}"
        )

        print(
            f"   GPT : "
            f"{analyse.get('compatibilite', 0)}"
            f"/100"
        )

        print(
            f"   FINAL : "
            f"{analyse['score_final']}"
            f"/100"
        )

        print(
            f"   Décision : "
            f"{analyse['decision']}"
        )

        print()

    # --------------------------------------------------------
    # BILAN
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("BILAN")
    print("=" * 72)

    print(
        f"✅ Migrées : "
        f"{migrees}"
    )

    print(
        f"♻️ Déjà au nouveau format : "
        f"{deja_ok}"
    )

    print(
        f"❌ Erreurs : "
        f"{erreurs}"
    )

    print(
        f"📚 Total : "
        f"{len(lignes)}"
    )

    print("=" * 72)
    print()


if __name__ == "__main__":
    migrer()