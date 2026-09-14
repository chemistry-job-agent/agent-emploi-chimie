import re
import shutil

from email import policy
from email.parser import BytesParser

from pathlib import Path

from urllib.parse import (
    parse_qs,
    unquote,
    urlparse
)

from bs4 import BeautifulSoup


INBOX = Path(
    "alertes_inbox"
)

ARCHIVE = Path(
    "alertes_archive"
)


# ============================================================
# OUTILS
# ============================================================

def nettoyer_texte(texte):
    if not texte:
        return ""

    return " ".join(
        str(texte)
        .replace("\xa0", " ")
        .split()
    )


def nettoyer_url(url):
    if not url:
        return ""

    url = (
        str(url)
        .strip()
        .replace("&amp;", "&")
    )

    url = unquote(
        url
    )

    return url.rstrip(
        ".,);]}>\"'"
    )


# ============================================================
# DÉTECTION SOURCE
# ============================================================

def detecter_source(url):
    url_min = url.lower()

    if "apec.fr" in url_min:
        return "Apec"

    if "linkedin.com" in url_min:
        return "LinkedIn"

    if (
        "indeed.fr" in url_min
        or "indeed.com" in url_min
    ):
        return "Indeed"

    return None


def est_url_offre(
    source,
    url
):
    url_min = url.lower()

    if source == "Apec":
        return (
            "/detail-offre/" in url_min
        )

    if source == "LinkedIn":
        return (
            "/jobs/view/" in url_min
        )

    if source == "Indeed":
        return (
            "/viewjob" in url_min
            or "jk=" in url_min
            or "vjk=" in url_min
        )

    return False


# ============================================================
# URLS DE REDIRECTION
# ============================================================

def chercher_url_embarquee(url):
    """
    Certaines alertes email utilisent un lien de tracking
    contenant l'URL réelle de l'offre à l'intérieur.
    """

    url_decodee = unquote(
        url
    )

    urls = re.findall(
        r"https?://[^\s\"'<>]+",
        url_decodee
    )

    for candidate in urls:
        candidate = nettoyer_url(
            candidate
        )

        source = detecter_source(
            candidate
        )

        if (
            source
            and est_url_offre(
                source,
                candidate
            )
        ):
            return candidate

    return url


# ============================================================
# IDENTIFIANT SOURCE
# ============================================================

def extraire_source_id(
    source,
    url
):
    if source == "Apec":

        match = re.search(
            r"/detail-offre/([^/?#]+)",
            url,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1)


    if source == "LinkedIn":

        match = re.search(
            r"/jobs/view/(?:[^/?#]*-)?(\d+)",
            url,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1)


    if source == "Indeed":

        params = parse_qs(
            urlparse(
                url
            ).query
        )

        for cle in (
            "jk",
            "vjk"
        ):
            valeurs = params.get(
                cle
            )

            if valeurs:
                return valeurs[0]


    # Fallback stable
    return url


# ============================================================
# LECTURE EML
# ============================================================

def lire_eml(chemin):
    with open(
        chemin,
        "rb"
    ) as fichier:

        message = BytesParser(
            policy=policy.default
        ).parse(
            fichier
        )

    html = []
    texte = []

    if message.is_multipart():

        for partie in message.walk():

            try:
                contenu = (
                    partie.get_content()
                )
            except Exception:
                continue

            type_contenu = (
                partie.get_content_type()
            )

            if (
                type_contenu
                == "text/html"
            ):
                html.append(
                    str(contenu)
                )

            elif (
                type_contenu
                == "text/plain"
            ):
                texte.append(
                    str(contenu)
                )

    else:

        try:
            contenu = (
                message.get_content()
            )

        except Exception:
            contenu = ""

        if (
            message.get_content_type()
            == "text/html"
        ):
            html.append(
                str(contenu)
            )

        else:
            texte.append(
                str(contenu)
            )

    if html:
        return "\n".join(
            html
        )

    return "\n".join(
        texte
    )


def lire_fichier(
    chemin
):
    if (
        chemin.suffix.lower()
        == ".eml"
    ):
        return lire_eml(
            chemin
        )

    return chemin.read_text(
        encoding="utf-8",
        errors="ignore"
    )


# ============================================================
# CRÉATION OFFRE
# ============================================================

def creer_offre(
    source,
    source_id,
    url,
    titre="",
    description=""
):
    titre = nettoyer_texte(
        titre
    )

    description = nettoyer_texte(
        description
    )

    if not titre:
        titre = (
            "Offre emploi chimie"
        )

    return {
        "source":
            source,

        "source_id":
            str(
                source_id
            ),

        "titre":
            titre,

        "entreprise":
            "",

        "lieu":
            "",

        "contrat":
            "",

        "description":
            description,

        "url":
            url,

        "date_publication":
            "",

        "experience":
            "",

        "salaire":
            "",

        "donnees_brutes":
            {
                "titre_alerte":
                    titre,

                "texte_alerte":
                    description,

                "url":
                    url
            }
    }


# ============================================================
# EXTRACTION HTML
# ============================================================

def extraire_html(
    contenu
):
    soup = BeautifulSoup(
        contenu,
        "html.parser"
    )

    offres = []

    vus = set()

    for lien in soup.find_all(
        "a",
        href=True
    ):
        url = nettoyer_url(
            lien.get(
                "href",
                ""
            )
        )

        url = chercher_url_embarquee(
            url
        )

        source = detecter_source(
            url
        )

        if not source:
            continue

        if not est_url_offre(
            source,
            url
        ):
            continue

        source_id = (
            extraire_source_id(
                source,
                url
            )
        )

        cle = (
            source,
            str(source_id)
        )

        if cle in vus:
            continue

        vus.add(
            cle
        )

        titre = nettoyer_texte(
            lien.get_text(
                " ",
                strip=True
            )
        )

        description = ""

        parent = lien

        # On remonte plusieurs niveaux
        # pour récupérer le bloc de l'annonce.
        for _ in range(4):

            if (
                parent is None
                or parent.parent is None
            ):
                break

            parent = parent.parent

            texte_parent = nettoyer_texte(
                parent.get_text(
                    " ",
                    strip=True
                )
            )

            if (
                len(texte_parent)
                > len(description)
            ):
                description = (
                    texte_parent
                )

            if (
                len(description)
                >= 500
            ):
                break

        offres.append(
            creer_offre(
                source=
                    source,

                source_id=
                    source_id,

                url=
                    url,

                titre=
                    titre,

                description=
                    description
            )
        )

    return offres


# ============================================================
# EXTRACTION TEXTE
# ============================================================

def extraire_texte(
    contenu
):
    urls = re.findall(
        r"https?://[^\s<>\"']+",
        contenu
    )

    offres = []

    vus = set()

    for url in urls:

        url = nettoyer_url(
            url
        )

        url = chercher_url_embarquee(
            url
        )

        source = detecter_source(
            url
        )

        if not source:
            continue

        if not est_url_offre(
            source,
            url
        ):
            continue

        source_id = (
            extraire_source_id(
                source,
                url
            )
        )

        cle = (
            source,
            str(source_id)
        )

        if cle in vus:
            continue

        vus.add(
            cle
        )

        offres.append(
            creer_offre(
                source=
                    source,

                source_id=
                    source_id,

                url=
                    url,

                description=
                    contenu
            )
        )

    return offres


# ============================================================
# ARCHIVAGE
# ============================================================

def archiver_fichier(
    chemin
):
    ARCHIVE.mkdir(
        exist_ok=True
    )

    destination = (
        ARCHIVE
        / chemin.name
    )

    compteur = 1

    while destination.exists():

        destination = (
            ARCHIVE
            / (
                f"{chemin.stem}_"
                f"{compteur}"
                f"{chemin.suffix}"
            )
        )

        compteur += 1

    shutil.move(
        str(chemin),
        str(destination)
    )


# ============================================================
# LECTURE DE L'INBOX
# ============================================================

def lire_alertes_locales(
    archiver=True
):
    INBOX.mkdir(
        exist_ok=True
    )

    ARCHIVE.mkdir(
        exist_ok=True
    )

    fichiers = []

    for extension in (
        "*.eml",
        "*.html",
        "*.htm",
        "*.txt"
    ):

        fichiers.extend(
            INBOX.glob(
                extension
            )
        )

    if not fichiers:
        return []

    toutes_offres = []

    print()

    print(
        "📨 ALERTES EMPLOI LOCALES"
    )

    for chemin in fichiers:

        print(
            f"📩 {chemin.name}"
        )

        try:
            contenu = lire_fichier(
                chemin
            )

            contenu_min = (
                contenu.lower()
            )

            if (
                "<html" in contenu_min
                or "<a " in contenu_min
            ):

                offres = extraire_html(
                    contenu
                )

            else:

                offres = extraire_texte(
                    contenu
                )

            print(
                f"   → "
                f"{len(offres)} "
                f"offre(s)"
            )

            toutes_offres.extend(
                offres
            )

            if archiver:
                archiver_fichier(
                    chemin
                )

        except Exception as erreur:

            print(
                f"   ❌ "
                f"{erreur}"
            )

    # ========================================================
    # DÉDOUBLONNAGE EXACT SOURCE + ID
    # ========================================================

    uniques = []

    vus = set()

    for offre in toutes_offres:

        cle = (
            offre.get(
                "source",
                ""
            ),

            offre.get(
                "source_id",
                ""
            )
        )

        if cle in vus:
            continue

        vus.add(
            cle
        )

        uniques.append(
            offre
        )

    return uniques