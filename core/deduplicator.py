import re
import unicodedata
from difflib import SequenceMatcher


def normaliser_texte(texte):

    if not texte:
        return ""

    texte = str(texte).lower().strip()

    texte = unicodedata.normalize(
        "NFKD",
        texte
    )

    texte = "".join(
        caractere
        for caractere in texte
        if not unicodedata.combining(caractere)
    )

    texte = re.sub(
        r"[^a-z0-9]+",
        " ",
        texte
    )

    texte = re.sub(
        r"\s+",
        " ",
        texte
    )

    return texte.strip()


def similarite_texte(
    texte_a,
    texte_b
):

    a = normaliser_texte(
        texte_a
    )

    b = normaliser_texte(
        texte_b
    )

    if not a or not b:
        return 0.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def score_doublon(
    offre_a,
    offre_b
):

    score = 0.0

    # -----------------------------
    # TITRE
    # -----------------------------

    titre = similarite_texte(
        offre_a.get(
            "titre",
            ""
        ),
        offre_b.get(
            "titre",
            ""
        )
    )

    score += titre * 0.45


    # -----------------------------
    # ENTREPRISE
    # -----------------------------

    entreprise = similarite_texte(
        offre_a.get(
            "entreprise",
            ""
        ),
        offre_b.get(
            "entreprise",
            ""
        )
    )

    score += entreprise * 0.30


    # -----------------------------
    # LIEU
    # -----------------------------

    lieu = similarite_texte(
        offre_a.get(
            "lieu",
            ""
        ),
        offre_b.get(
            "lieu",
            ""
        )
    )

    score += lieu * 0.15


    # -----------------------------
    # DESCRIPTION
    # -----------------------------

    description = similarite_texte(
        offre_a.get(
            "description",
            ""
        )[:1500],
        offre_b.get(
            "description",
            ""
        )[:1500]
    )

    score += description * 0.10


    return round(
        score,
        3
    )


def sont_doublons(
    offre_a,
    offre_b,
    seuil=0.78
):

    # Même source + même ID :
    # doublon certain

    if (
        offre_a.get("source")
        == offre_b.get("source")
        and
        offre_a.get("source_id")
        == offre_b.get("source_id")
        and
        offre_a.get("source_id")
    ):

        return True


    score = score_doublon(
        offre_a,
        offre_b
    )

    return score >= seuil


def dedoublonner_offres(
    offres,
    seuil=0.78
):

    offres_uniques = []


    for offre in offres:

        doublon_trouve = False


        for offre_existante in offres_uniques:

            if sont_doublons(
                offre,
                offre_existante,
                seuil=seuil
            ):

                doublon_trouve = True


                # On mémorise toutes les sources
                sources = offre_existante.get(
                    "sources",
                    [
                        offre_existante.get(
                            "source",
                            ""
                        )
                    ]
                )


                nouvelle_source = offre.get(
                    "source",
                    ""
                )


                if (
                    nouvelle_source
                    and
                    nouvelle_source not in sources
                ):

                    sources.append(
                        nouvelle_source
                    )


                offre_existante[
                    "sources"
                ] = sources


                # On garde l'URL si la première
                # n'en avait pas

                if (
                    not offre_existante.get(
                        "url"
                    )
                    and offre.get(
                        "url"
                    )
                ):

                    offre_existante[
                        "url"
                    ] = offre["url"]


                break


        if not doublon_trouve:

            nouvelle_offre = dict(
                offre
            )

            nouvelle_offre[
                "sources"
            ] = [
                offre.get(
                    "source",
                    ""
                )
            ]

            offres_uniques.append(
                nouvelle_offre
            )


    return offres_uniques