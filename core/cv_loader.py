from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader


DOSSIER_CV = Path("cv")

CV_INGENIEUR = (
    DOSSIER_CV
    / "Lilian_LOISONS_Ingenieur_Chimiste_CV.pdf"
)

CV_TECHNICIEN = (
    DOSSIER_CV
    / "Lilian_LOISONS_Technicien_Chimiste_CV.pdf"
)


def extraire_texte_pdf(chemin):

    if not chemin.exists():

        raise FileNotFoundError(
            f"CV introuvable : {chemin}"
        )

    lecteur = PdfReader(
        str(chemin)
    )

    pages = []

    for page in lecteur.pages:

        texte = page.extract_text()

        if texte:

            pages.append(
                texte.strip()
            )

    texte_complet = "\n".join(
        pages
    )

    if not texte_complet.strip():

        raise RuntimeError(
            f"Aucun texte extrait de : {chemin}"
        )

    return texte_complet


@lru_cache(maxsize=1)
def charger_cvs():

    return {

        "INGENIEUR": {
            "chemin":
                str(CV_INGENIEUR),

            "texte":
                extraire_texte_pdf(
                    CV_INGENIEUR
                )
        },

        "TECHNICIEN": {
            "chemin":
                str(CV_TECHNICIEN),

            "texte":
                extraire_texte_pdf(
                    CV_TECHNICIEN
                )
        }
    }