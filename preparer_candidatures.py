from core.database import (
    initialiser_base
)

from core.candidature_builder import (
    recuperer_offres_a_preparer,
    candidature_existe,
    preparer_candidature
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_CANDIDATURES_PAR_LANCEMENT = 2

GENERER_LETTRES = True


# ============================================================
# PROGRAMME
# ============================================================

def main():

    print()
    print("=" * 78)

    print(
        "PRÉPARATION AUTOMATIQUE DES CANDIDATURES"
    )

    print("=" * 78)

    print()

    initialiser_base()

    offres = recuperer_offres_a_preparer()

    print(
        f"Offres PRIORITE_HAUTE / POSTULER : "
        f"{len(offres)}"
    )

    nouvelles = []

    deja_preparees = 0

    for offre in offres:

        if candidature_existe(
            offre[
                "offre_id"
            ]
        ):

            deja_preparees += 1

            continue

        nouvelles.append(
            offre
        )

    print(
        f"Déjà préparées : "
        f"{deja_preparees}"
    )

    print(
        f"À préparer : "
        f"{len(nouvelles)}"
    )

    lot = nouvelles[
        :MAX_CANDIDATURES_PAR_LANCEMENT
    ]

    print(
        f"Préparation de "
        f"{len(lot)} candidature(s)"
    )

    print()

    reussies = 0
    erreurs = 0

    for numero, offre in enumerate(
        lot,
        start=1
    ):

        print("=" * 78)

        print(
            f"[{numero}/{len(lot)}] "
            f"{offre['titre']}"
        )

        print(
            f"Entreprise : "
            f"{offre['entreprise']}"
        )

        print(
            f"Score final : "
            f"{offre['score_final']}/100"
        )

        print(
            f"Décision : "
            f"{offre['decision']}"
        )

        print(
            f"CV : "
            f"{offre['cv_recommande']}"
        )

        print()

        try:

            print(
                "📁 Création du dossier..."
            )

            if GENERER_LETTRES:

                print(
                    "🧠 Génération de la lettre "
                    "avec GPT-OSS..."
                )

            resultat = (
                preparer_candidature(
                    offre,
                    generer_lettre_ia=
                        GENERER_LETTRES
                )
            )

            if resultat is None:

                print(
                    "⚠️ Candidature non éligible."
                )

                continue

            print()

            print(
                "✅ Candidature préparée."
            )

            print(
                f"📂 "
                f"{resultat['dossier']}"
            )

            print(
                "🔒 Aucun envoi automatique."
            )

            print(
                "👤 Validation humaine requise."
            )

            print()

            reussies += 1

        except Exception as erreur:

            erreurs += 1

            print(
                f"❌ Erreur : "
                f"{erreur}"
            )

            print()

    print("=" * 78)

    print(
        "BILAN"
    )

    print("=" * 78)

    print(
        f"✅ Préparées : "
        f"{reussies}"
    )

    print(
        f"❌ Erreurs : "
        f"{erreurs}"
    )

    print(
        f"♻️ Déjà existantes : "
        f"{deja_preparees}"
    )

    print()

    print(
        "Les dossiers sont disponibles dans :"
    )

    print(
        r"C:\Agent-emploi-chimie\candidatures"
    )

    print()


if __name__ == "__main__":
    main()