from sources.france_travail import (
    rechercher_offres
)

from sources.apec_alerts import (
    extraire_urls_apec,
    creer_offre_apec_depuis_email
)

from sources.linkedin_alerts import (
    extraire_urls_linkedin,
    creer_offre_linkedin
)

from sources.indeed_alerts import (
    extraire_urls_indeed,
    creer_offre_indeed
)

from core.normalizer import (
    normaliser_liste_france_travail
)

from core.deduplicator import (
    dedoublonner_offres
)


def collecter_france_travail(
    recherches,
    nombre_par_recherche=20
):

    offres_brutes = rechercher_offres(
        recherches=recherches,
        nombre_par_recherche=nombre_par_recherche
    )

    return normaliser_liste_france_travail(
        offres_brutes
    )


def collecter_alerte_apec(alerte):

    contenu = alerte.get(
        "contenu",
        ""
    )

    urls = extraire_urls_apec(
        contenu
    )

    offres = []

    for url in urls:

        offre = creer_offre_apec_depuis_email(
            url=url,
            titre=alerte.get(
                "titre",
                ""
            ),
            entreprise=alerte.get(
                "entreprise",
                ""
            ),
            lieu=alerte.get(
                "lieu",
                ""
            ),
            description=alerte.get(
                "description",
                ""
            )
        )

        offres.append(
            offre
        )

    return offres


def collecter_alerte_linkedin(alerte):

    contenu = alerte.get(
        "contenu",
        ""
    )

    urls = extraire_urls_linkedin(
        contenu
    )

    offres = []

    for url in urls:

        offre = creer_offre_linkedin(
            url=url,
            titre=alerte.get(
                "titre",
                ""
            ),
            entreprise=alerte.get(
                "entreprise",
                ""
            ),
            lieu=alerte.get(
                "lieu",
                ""
            ),
            description=alerte.get(
                "description",
                ""
            ),
            contrat=alerte.get(
                "contrat",
                ""
            )
        )

        offres.append(
            offre
        )

    return offres


def collecter_alerte_indeed(alerte):

    contenu = alerte.get(
        "contenu",
        ""
    )

    urls = extraire_urls_indeed(
        contenu
    )

    offres = []

    for url in urls:

        offre = creer_offre_indeed(
            url=url,
            titre=alerte.get(
                "titre",
                ""
            ),
            entreprise=alerte.get(
                "entreprise",
                ""
            ),
            lieu=alerte.get(
                "lieu",
                ""
            ),
            description=alerte.get(
                "description",
                ""
            ),
            contrat=alerte.get(
                "contrat",
                ""
            )
        )

        offres.append(
            offre
        )

    return offres


def collecter_alertes(
    alertes
):

    offres = []

    for alerte in alertes:

        source = (
            alerte.get(
                "source",
                ""
            )
            .strip()
            .lower()
        )

        if source == "apec":

            offres.extend(
                collecter_alerte_apec(
                    alerte
                )
            )

        elif source == "linkedin":

            offres.extend(
                collecter_alerte_linkedin(
                    alerte
                )
            )

        elif source == "indeed":

            offres.extend(
                collecter_alerte_indeed(
                    alerte
                )
            )

    return offres


def collecter_toutes_les_offres(
    recherches_france_travail,
    alertes=None,
    nombre_par_recherche=20
):

    toutes_les_offres = []

    # ==========================================
    # FRANCE TRAVAIL
    # ==========================================

    print()
    print("🇫🇷 France Travail")

    offres_ft = collecter_france_travail(
        recherches=recherches_france_travail,
        nombre_par_recherche=nombre_par_recherche
    )

    print(
        f"   → {len(offres_ft)} offre(s)"
    )

    toutes_les_offres.extend(
        offres_ft
    )


    # ==========================================
    # ALERTES
    # ==========================================

    if alertes:

        print()
        print("📨 Alertes emploi")

        offres_alertes = collecter_alertes(
            alertes
        )

        print(
            f"   → {len(offres_alertes)} offre(s)"
        )

        toutes_les_offres.extend(
            offres_alertes
        )


    # ==========================================
    # DÉDOUBLONNAGE
    # ==========================================

    avant = len(
        toutes_les_offres
    )

    offres_uniques = dedoublonner_offres(
        toutes_les_offres
    )

    apres = len(
        offres_uniques
    )

    print()
    print(
        f"🔗 Offres avant dédoublonnage : "
        f"{avant}"
    )

    print(
        f"✅ Offres uniques : "
        f"{apres}"
    )

    print(
        f"♻️ Doublons supprimés : "
        f"{avant - apres}"
    )

    return offres_uniques