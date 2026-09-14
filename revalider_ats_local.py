import json

from pathlib import Path

from core.ats_guard import (
    securiser_analyse_ats
)


DOSSIER = (
    Path("candidatures")
    / "ats_tests"
)


def trouver_dernier_test():

    fichiers = [
        fichier
        for fichier in DOSSIER.glob(
            "ats_offre_*.json"
        )
        if not fichier.name.endswith(
            "_securise.json"
        )
    ]

    if not fichiers:
        raise FileNotFoundError(
            "Aucun test ATS trouvé."
        )

    return max(
        fichiers,
        key=lambda fichier:
            fichier.stat().st_mtime
    )


def afficher_liste(
    titre,
    elements
):

    print()
    print(titre)
    print("-" * 70)

    if not elements:
        print("Aucun.")
        return

    for element in elements:
        print(
            f"- {element}"
        )


def main():

    print()
    print("=" * 78)
    print("REVALIDATION ATS LOCALE V2 - SANS GPT")
    print("=" * 78)

    source = trouver_dernier_test()

    print()
    print(
        f"Source : {source}"
    )

    analyse = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    resultat = securiser_analyse_ats(
        analyse
    )

    afficher_liste(
        "INTITULES CIBLES AUTORISES",
        resultat.get(
            "intitules_cibles_autorises",
            []
        )
    )

    afficher_liste(
        "COMPETENCES CONFIRMEES",
        resultat.get(
            "competences_confirmees_cv",
            []
        )
    )

    afficher_liste(
        "COMPETENCES A FORMULATION PROTEGEE",
        resultat.get(
            "competences_protegees_cv",
            []
        )
    )

    afficher_liste(
        "QUALITES CONFIRMEES",
        resultat.get(
            "qualites_confirmees_cv",
            []
        )
    )

    afficher_liste(
        "TERMES CONTEXTUELS - VALIDATION HUMAINE",
        resultat.get(
            "termes_contextuels_a_valider",
            []
        )
    )

    afficher_liste(
        "MOTS-CLES REFUSES",
        resultat.get(
            "mots_cles_refuses",
            []
        )
    )

    afficher_liste(
        "MOTS-CLES INCONNUS",
        resultat.get(
            "mots_cles_inconnus",
            []
        )
    )

    afficher_liste(
        "MANQUES REELS OBLIGATOIRES / IMPORTANTS",
        resultat.get(
            "manques_reels",
            []
        )
    )

    afficher_liste(
        "CRITERES BONUS ABSENTS",
        resultat.get(
            "bonus_absents",
            []
        )
    )

    print()
    print("PREUVES IA BLOQUEES")
    print("-" * 70)

    preuves = resultat.get(
        "preuves_bloquees",
        []
    )

    if not preuves:

        print(
            "Aucune."
        )

    else:

        for preuve in preuves:

            print(
                f"- {preuve.get('critere', '')}"
            )

            termes = preuve.get(
                "termes",
                []
            )

            if termes:

                print(
                    "  Termes détectés : "
                    + ", ".join(
                        termes
                    )
                )

    afficher_liste(
        "ADAPTATIONS CV SECURISEES",
        resultat.get(
            "adaptations_cv",
            []
        )
    )

    print()
    print("RESUME SECURISE")
    print("-" * 70)

    print(
        resultat.get(
            "resume_ats",
            ""
        )
    )

    destination = source.with_name(
        source.stem
        + "_securise.json"
    )

    destination.write_text(
        json.dumps(
            resultat,
            ensure_ascii=False,
            indent=2,
            default=str
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 78)

    print(
        f"Résultat : {destination}"
    )

    print(
        "Aucun appel GPT-OSS effectué."
    )

    print("=" * 78)
    print()


if __name__ == "__main__":
    main()