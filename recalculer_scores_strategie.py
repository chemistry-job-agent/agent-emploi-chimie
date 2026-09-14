import json

from ai.analyzer import ANALYSE_VERSION
from core.database import connexion
from core.scorer import calculer_score_final


# ============================================================
# RECALCUL DES SCORES
# ============================================================

def main():

    print()
    print("=" * 78)
    print("RECALCUL DES SCORES AVEC LA STRATEGIE INTERNATIONALE")
    print("=" * 78)
    print()

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

                a.id AS analyse_id,
                a.analyse_version,
                a.resultat_json

            FROM offres AS o

            INNER JOIN analyses AS a
                ON a.offre_id = o.id

            WHERE a.analyse_version = ?

            ORDER BY o.id
            """,
            (
                ANALYSE_VERSION,
            )
        ).fetchall()

        print(
            f"Version d'analyse : {ANALYSE_VERSION}"
        )

        print(
            f"Analyses trouvées : {len(lignes)}"
        )

        print()

        mises_a_jour = 0
        erreurs = 0

        for ligne in lignes:

            try:

                # ------------------------------------------------
                # ANALYSE IA DEJA EN BASE
                # ------------------------------------------------

                analyse = json.loads(
                    ligne["resultat_json"]
                )

                # ------------------------------------------------
                # RECONSTRUCTION DE L'OFFRE
                # ------------------------------------------------

                offre = {
                    "titre":
                        ligne["titre"] or "",

                    "entreprise":
                        ligne["entreprise"] or "",

                    "lieu":
                        ligne["lieu"] or "",

                    "contrat":
                        ligne["contrat"] or "",

                    "description":
                        ligne["description"] or "",

                    "date_publication":
                        ligne["date_publication"] or "",

                    "experience":
                        ligne["experience"] or "",

                    "salaire":
                        ligne["salaire"] or "",

                    "url":
                        ligne["url_principale"] or ""
                }

                # ------------------------------------------------
                # NOUVEAU SCORING
                # ------------------------------------------------

                nouveau_score = calculer_score_final(
                    offre,
                    analyse
                )

                # ------------------------------------------------
                # AJOUT DES NOUVELLES INFORMATIONS AU JSON
                # ------------------------------------------------

                analyse.update(
                    nouveau_score
                )

                resultat_json = json.dumps(
                    analyse,
                    ensure_ascii=False,
                    indent=2,
                    default=str
                )

                # ------------------------------------------------
                # MISE A JOUR ANALYSE
                # ------------------------------------------------

                conn.execute(
                    """
                    UPDATE analyses

                    SET resultat_json = ?

                    WHERE id = ?
                    """,
                    (
                        resultat_json,
                        ligne["analyse_id"]
                    )
                )

                # ------------------------------------------------
                # MISE A JOUR OFFRE
                # ------------------------------------------------

                conn.execute(
                    """
                    UPDATE offres

                    SET
                        score_final = ?,
                        statut = ?

                    WHERE id = ?
                    """,
                    (
                        nouveau_score[
                            "score_final"
                        ],

                        nouveau_score[
                            "decision"
                        ],

                        ligne[
                            "offre_id"
                        ]
                    )
                )

                mises_a_jour += 1

                # ------------------------------------------------
                # AFFICHAGE
                # ------------------------------------------------

                print(
                    f"✅ {ligne['titre']}"
                )

                print(
                    f"   Entreprise : "
                    f"{ligne['entreprise']}"
                )

                print(
                    f"   Lieu : "
                    f"{ligne['lieu']}"
                )

                print(
                    f"   Pays : "
                    f"{nouveau_score['pays']}"
                )

                print(
                    f"   Pipeline : "
                    f"{nouveau_score['pipeline']}"
                )

                print(
                    f"   Géographie : "
                    f"{nouveau_score['score_geographique']}/100"
                )

                print(
                    f"   Opportunité : "
                    f"{nouveau_score['score_opportunite']}/100"
                )

                print(
                    f"   Bonus stratégique : "
                    f"+{nouveau_score['bonus_strategique']}"
                )

                print(
                    f"   Score final : "
                    f"{nouveau_score['score_final']}/100"
                )

                print(
                    f"   Décision : "
                    f"{nouveau_score['decision']}"
                )

                print()

            except Exception as erreur:

                erreurs += 1

                print(
                    f"❌ Offre "
                    f"{ligne['offre_id']} : "
                    f"{erreur}"
                )

                print()

        # --------------------------------------------------------
        # SAUVEGARDE
        # --------------------------------------------------------

        conn.commit()

    # ============================================================
    # BILAN
    # ============================================================

    print("=" * 78)
    print("BILAN")
    print("=" * 78)

    print(
        f"✅ Scores recalculés : "
        f"{mises_a_jour}"
    )

    print(
        f"❌ Erreurs : "
        f"{erreurs}"
    )

    print()

    print(
        "Aucun appel GPT-OSS n'a été effectué."
    )

    print()


if __name__ == "__main__":
    main()