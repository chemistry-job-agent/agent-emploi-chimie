import argparse
import json
import re
import shutil
import subprocess

from pathlib import Path

from pypdf import PdfReader

from core.ats_analyzer import analyser_ats
from core.candidature_builder import (
    recuperer_offres_a_preparer,
    candidature_existe,
    creer_dossier_candidature,
    enregistrer_candidature,
)
from core.cv_ats_plan import construire_plan_cv
from core.cv_docx_builder import generer_cv_docx


# ============================================================
# CONFIGURATION
# ============================================================

MIN_TEXTE_PDF = 900


# ============================================================
# OUTILS
# ============================================================

def nettoyer_nom_fichier(texte):

    texte = str(
        texte
        or "offre"
    )

    texte = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        texte,
    )

    texte = re.sub(
        r"\s+",
        "_",
        texte,
    )

    return texte.strip(
        "._"
    )[:100]


def sauvegarder_json(
    chemin,
    donnees,
):

    Path(
        chemin
    ).write_text(
        json.dumps(
            donnees,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


# ============================================================
# NORMALISATION OFFRE
# ============================================================

def normaliser_offre(
    offre
):

    offre = dict(
        offre
    )

    offre_id = (
        offre.get(
            "offre_id"
        )
        or offre.get(
            "id"
        )
    )

    if not offre_id:

        raise RuntimeError(
            "Identifiant de l'offre introuvable."
        )

    # Compatibilité avec les modules qui utilisent "id"
    # et ceux qui utilisent "offre_id".
    offre[
        "offre_id"
    ] = offre_id

    offre[
        "id"
    ] = offre_id

    return offre


# ============================================================
# CHOIX DU CV
# ============================================================

def choisir_cv_recommande(
    offre
):

    valeur = str(
        offre.get(
            "cv_recommande",
            ""
        )
        or ""
    ).strip()

    valeur_maj = valeur.upper()

    if "TECH" in valeur_maj:

        return "TECHNICIEN"

    if "ING" in valeur_maj:

        return "INGENIEUR"

    texte = " ".join(
        [
            str(
                offre.get(
                    "titre",
                    ""
                )
            ),
            str(
                offre.get(
                    "type_poste",
                    ""
                )
            ),
        ]
    ).lower()

    if (
        "technicien"
        in texte
        or "assistant"
        in texte
    ):

        return "TECHNICIEN"

    return "INGENIEUR"


# ============================================================
# LIBREOFFICE
# ============================================================

def trouver_libreoffice():

    candidats = [
        Path(
            r"C:\Program Files\LibreOffice\program\soffice.exe"
        ),
        Path(
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ),
    ]

    for chemin in candidats:

        if chemin.exists():

            return str(
                chemin
            )

    chemin = shutil.which(
        "soffice"
    )

    if chemin:

        return chemin

    chemin = shutil.which(
        "libreoffice"
    )

    if chemin:

        return chemin

    raise FileNotFoundError(
        "LibreOffice introuvable."
    )


def convertir_docx_pdf(
    chemin_docx
):

    chemin_docx = Path(
        chemin_docx
    ).resolve()

    dossier = chemin_docx.parent

    soffice = trouver_libreoffice()

    resultat = subprocess.run(
        [
            soffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(
                dossier
            ),
            str(
                chemin_docx
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=90,
    )

    chemin_pdf = (
        dossier
        / (
            chemin_docx.stem
            + ".pdf"
        )
    )

    if not chemin_pdf.exists():

        raise RuntimeError(
            "Conversion LibreOffice échouée.\n"
            f"{resultat.stdout}\n"
            f"{resultat.stderr}"
        )

    return chemin_pdf


# ============================================================
# CONTROLE PDF
# ============================================================

def controler_pdf(
    chemin_pdf
):

    lecteur = PdfReader(
        str(
            chemin_pdf
        )
    )

    textes = []

    for page in lecteur.pages:

        textes.append(
            page.extract_text()
            or ""
        )

    texte = "\n".join(
        textes
    ).strip()

    texte_normalise = re.sub(
        r"\s+",
        " ",
        texte.lower(),
    )

    expressions_interdites = [
        "maîtrise de la hplc",
        "maitrise de la hplc",
        "expertise hplc",
        "expert hplc",
        "maîtrise du lc-ms",
        "maitrise du lc-ms",
        "expertise lc-ms",
        "expert lc-ms",
    ]

    survente_hplc = any(
        expression
        in texte_normalise
        for expression
        in expressions_interdites
    )

    controles = {
        "nombre_pages":
            len(
                lecteur.pages
            ),

        "longueur_texte":
            len(
                texte
            ),

        "une_page":
            len(
                lecteur.pages
            )
            == 1,

        "texte_suffisant":
            len(
                texte
            )
            >= MIN_TEXTE_PDF,

        "nom_present":
            (
                "lilian"
                in texte_normalise
                and "loisons"
                in texte_normalise
            ),

        "email_present":
            "@"
            in texte,

        "hplc_lcms_non_survendus":
            not survente_hplc,
    }

    controles[
        "controle_technique_ok"
    ] = all(
        [
            controles[
                "une_page"
            ],
            controles[
                "texte_suffisant"
            ],
            controles[
                "nom_present"
            ],
            controles[
                "email_present"
            ],
            controles[
                "hplc_lcms_non_survendus"
            ],
        ]
    )

    return controles


# ============================================================
# NOTE DE VALIDATION
# ============================================================

def creer_note_validation(
    offre,
    dossier,
    chemin_pdf,
    controle,
):

    chemin = (
        Path(
            dossier
        )
        / "A_VALIDER_AVANT_ENVOI.txt"
    )

    texte = f"""VALIDATION HUMAINE OBLIGATOIRE

Offre ID : {offre.get("offre_id")}
Poste : {offre.get("titre", "")}
Entreprise : {offre.get("entreprise", "")}
Lieu : {offre.get("lieu", "")}
URL : {offre.get("url", "")}

CV PDF :
{chemin_pdf}

Contrôle technique :
{"OK" if controle.get("controle_technique_ok") else "A VERIFIER"}

Avant de candidater :

1. Ouvrir le PDF.
2. Vérifier visuellement la mise en page.
3. Relire le contenu.
4. Vérifier qu'aucune compétence n'est inventée.
5. Vérifier HPLC / LC-MS.
6. Vérifier entreprise, poste et lieu.
7. Décider manuellement si la candidature doit être envoyée.

AUCUNE CANDIDATURE N'A ETE ENVOYEE AUTOMATIQUEMENT.
"""

    chemin.write_text(
        texte,
        encoding="utf-8",
    )

    return chemin


# ============================================================
# PREPARATION D'UNE CANDIDATURE
# ============================================================

def preparer_une_candidature(
    offre
):

    offre = normaliser_offre(
        offre
    )

    offre_id = offre[
        "offre_id"
    ]

    titre = str(
        offre.get(
            "titre",
            ""
        )
        or ""
    )

    entreprise = str(
        offre.get(
            "entreprise",
            ""
        )
        or ""
    )

    print()
    print("=" * 78)

    print(
        f"OFFRE {offre_id}"
    )

    print(
        titre
    )

    print(
        f"{entreprise} - "
        f"{offre.get('lieu', '')}"
    )

    # --------------------------------------------------------
    # EXISTANTE
    # --------------------------------------------------------

    if candidature_existe(
        offre_id
    ):

        print(
            "♻️ Candidature déjà préparée."
        )

        return "DEJA_PREPAREE"

    # --------------------------------------------------------
    # CV RECOMMANDE
    # --------------------------------------------------------

    cv_recommande = choisir_cv_recommande(
        offre
    )

    print(
        f"📄 CV recommandé : "
        f"{cv_recommande}"
    )

    # --------------------------------------------------------
    # ATS
    # --------------------------------------------------------

    print(
        "🔎 Analyse ATS..."
    )

    analyse_ats = analyser_ats(
        offre,
        cv_recommande,
    )

    if not isinstance(
        analyse_ats,
        dict,
    ):

        raise RuntimeError(
            "Analyse ATS invalide."
        )

    # --------------------------------------------------------
    # PLAN
    # --------------------------------------------------------

    print(
        "🛡️ Plan CV sécurisé..."
    )

    plan = construire_plan_cv(
        offre,
        analyse_ats,
        cv_recommande,
    )

    if not isinstance(
        plan,
        dict,
    ):

        raise RuntimeError(
            "Plan CV ATS invalide."
        )

    # --------------------------------------------------------
    # DOSSIER
    # --------------------------------------------------------

    dossier = Path(
        creer_dossier_candidature(
            offre
        )
    )

    dossier.mkdir(
        parents=True,
        exist_ok=True,
    )

    sauvegarder_json(
        dossier
        / "offre.json",
        offre,
    )

    sauvegarder_json(
        dossier
        / "analyse_ats.json",
        analyse_ats,
    )

    sauvegarder_json(
        dossier
        / "plan_cv_ats.json",
        plan,
    )

    # --------------------------------------------------------
    # NOM DU CV
    # --------------------------------------------------------

    nom_entreprise = nettoyer_nom_fichier(
        entreprise
        or "Entreprise"
    )

    nom_poste = nettoyer_nom_fichier(
        titre
        or "Poste"
    )

    nom_base = (
        f"CV_ATS_"
        f"{nom_entreprise}_"
        f"{nom_poste}_"
        f"offre_{offre_id}"
    )

    chemin_docx = (
        dossier
        / f"{nom_base}.docx"
    )

    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    print(
        "📝 Génération DOCX..."
    )

    generer_cv_docx(
        offre,
        plan,
        chemin_docx,
    )

    if not chemin_docx.exists():

        raise RuntimeError(
            "DOCX non créé."
        )

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    print(
        "📕 Conversion PDF..."
    )

    chemin_pdf = convertir_docx_pdf(
        chemin_docx
    )

    # --------------------------------------------------------
    # CONTROLE
    # --------------------------------------------------------

    print(
        "🔍 Contrôle final..."
    )

    controle = controler_pdf(
        chemin_pdf
    )

    sauvegarder_json(
        dossier
        / "controle_cv_ats.json",
        controle,
    )

    note = creer_note_validation(
        offre,
        dossier,
        chemin_pdf,
        controle,
    )

    # --------------------------------------------------------
    # ENREGISTREMENT
    # --------------------------------------------------------

    enregistrer_candidature(
    offre_id,
    str(
        chemin_pdf
    ),
    dossier,
)

    print()
    print(
        f"✅ DOCX : {chemin_docx}"
    )

    print(
        f"✅ PDF  : {chemin_pdf}"
    )

    print(
        f"👁️ Validation : {note}"
    )

    print(
        f"📄 Pages : "
        f"{controle['nombre_pages']}"
    )

    print(
        f"🔤 Texte : "
        f"{controle['longueur_texte']} caractères"
    )

    if controle[
        "controle_technique_ok"
    ]:

        print(
            "✅ CONTROLE_TECHNIQUE_OK"
        )

        return "A_VALIDER_HUMAINEMENT"

    print(
        "⚠️ CONTROLE_TECHNIQUE_A_VERIFIER"
    )

    return "CONTROLE_A_VERIFIER"


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max",
        type=int,
        default=1,
    )

    args = parser.parse_args()

    print()
    print("=" * 78)
    print(
        "PREPARATION AUTOMATIQUE DES CANDIDATURES ATS"
    )
    print("=" * 78)

    offres = list(
        recuperer_offres_a_preparer()
    )

    print()
    print(
        f"📋 Offres candidates : "
        f"{len(offres)}"
    )

    if not offres:

        return

    succes = 0
    deja = 0
    echecs = 0

    selection = offres[
        :max(
            1,
            args.max,
        )
    ]

    for offre in selection:

        try:

            statut = preparer_une_candidature(
                offre
            )

            if statut == "DEJA_PREPAREE":

                deja += 1

            else:

                succes += 1

        except Exception as erreur:

            echecs += 1

            print()
            print(
                "❌ ERREUR"
            )

            print(
                str(
                    erreur
                )
            )

    print()
    print("=" * 78)
    print("BILAN")
    print("=" * 78)

    print(
        f"✅ Préparées : {succes}"
    )

    print(
        f"♻️ Déjà préparées : {deja}"
    )

    print(
        f"❌ Échecs : {echecs}"
    )

    print()
    print(
        "🚫 Aucune candidature envoyée."
    )

    print(
        "👁️ Validation humaine obligatoire."
    )


if __name__ == "__main__":
    main()