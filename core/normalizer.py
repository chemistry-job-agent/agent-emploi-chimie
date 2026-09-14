def normaliser_offre_france_travail(offre):

    entreprise = offre.get(
        "entreprise",
        {}
    )

    lieu = offre.get(
        "lieuTravail",
        {}
    )

    origine = offre.get(
        "origineOffre",
        {}
    )

    return {
        "source": "France Travail",

        "source_id": str(
            offre.get(
                "id",
                ""
            )
        ),

        "titre": offre.get(
            "intitule",
            ""
        ),

        "entreprise": entreprise.get(
            "nom",
            ""
        ),

        "lieu": lieu.get(
            "libelle",
            ""
        ),

        "contrat": offre.get(
            "typeContratLibelle",
            ""
        ),

        "description": offre.get(
            "description",
            ""
        ),

        "url": origine.get(
            "urlOrigine",
            ""
        ),

        "date_publication": offre.get(
            "dateCreation",
            ""
        ),

        "experience": offre.get(
            "experienceLibelle",
            ""
        ),

        "salaire": offre.get(
            "salaire",
            {}
        ).get(
            "libelle",
            ""
        ),

        "donnees_brutes": offre
    }


def normaliser_liste_france_travail(offres):

    return [
        normaliser_offre_france_travail(
            offre
        )
        for offre in offres
    ]