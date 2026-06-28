# -*- coding: utf-8 -*-
"""
CR Fibre v4.2 — Définition des modèles d'intervention FTTH (data-driven) et
moteur de rendu au FORMAT RÉEL des tickets terrain.

Format produit (calqué sur les vrais CR du technicien) :

    {equipe}
    {code}
    {statut}

    {corps}

    Merci de passer la panne en travaux.     <- auto si statut « Travaux »
    DPR : {dpr}                               <- si renseigné
    Cordialement
    {SIGN_NAME}:{SIGN_PHONE}                  <- signature auto (env)

4 modèles : 1 « CR rapide » texte-libre (défaut, dictée vocale) + 3 accélérateurs
structurés (coupure→travaux, reprise/jarretière→clos, gros chantier soudures).

Pour modifier/ajouter un modèle : éditer ce seul fichier.
"""
import os
import re

OPERATEURS = ["Orange", "SFR", "Free", "Bouygues", "Autre"]
NATURE_COUPURE = ["Coupure", "Câble impacté", "Fibre HS", "Vandalisme", "Tubes coupés à ras"]

# -- Modèles ------------------------------------------------------------------

TEMPLATES = [
    {
        "key": "cr_rapide",
        "label": "CR rapide (texte libre)",
        "fields": [
            {"name": "corps", "label": "Compte-rendu (dictée 🎤)", "type": "textarea", "required": True,
             "ph": "Suite intervention ... clients UP, test AMS avec Nova. RAS, intervention clôturée."},
        ],
        "corps": "{corps}",
    },
    {
        "key": "coupure_travaux",
        "label": "Coupure / OTDR → Travaux",
        "fields": [
            {"name": "distance_m", "label": "Distance du défaut (m)", "type": "number", "ph": "43"},
            {"name": "point", "label": "Point (BE / PBO / PM)", "type": "text", "ph": "PBO-16"},
            {"name": "nature", "label": "Nature", "type": "select", "options": NATURE_COUPURE},
            {"name": "action", "label": "Action requise", "type": "text", "ph": "remplacer le câble entre BE et BI"},
            {"name": "corps", "label": "Détail (dictée 🎤)", "type": "textarea",
             "ph": "Suite intervention après test OTDR ..."},
        ],
        "corps": (
            "Suite à intervention après le test OTDR nous avons constaté un défaut ({nature}) à {distance_m} m au {point}.\n"
            "{corps}\n"
            "Action : {action}."
        ),
    },
    {
        "key": "reprise_clos",
        "label": "Reprise / jarretière / soudure → Clos",
        "fields": [
            {"name": "constat", "label": "Constat", "type": "text", "ph": "jarretière coupée / fibre cassée au BE"},
            {"name": "action", "label": "Action réalisée", "type": "text", "ph": "remplacement jarretière / soudure et remise en conformité"},
            {"name": "test", "label": "Test", "type": "select", "options": ["AMS avec Nova", "AMS", "Mesure photo", "N/A"]},
            {"name": "continuite", "label": "Continuité PM ↔ PBO/BE", "type": "select", "options": ["OK", "KO", "N/A"]},
            {"name": "corps", "label": "Détail (dictée 🎤)", "type": "textarea",
             "ph": "Suite intervention ..."},
        ],
        "corps": (
            "Suite intervention nous trouvons {constat}.\n"
            "Après {action}, les clients sont UP (test {test}).\n"
            "{corps}\n"
            "Continuité {continuite} entre PM et PBO."
        ),
    },
    {
        "key": "chantier_soudures",
        "label": "Gros chantier soudures (multi-BE) → Travaux terminé",
        "fields": [
            {"name": "site", "label": "Site / adresse", "type": "text", "ph": "6 Place des Érables, 94470 Boissy-Saint-Léger"},
            {"name": "cable_tire", "label": "Câble tiré", "type": "text", "ph": "150 m de 72 FO Module 6"},
            {"name": "total_soudures", "label": "Total soudures (FO)", "type": "number", "ph": "96"},
            {"name": "continuite", "label": "Continuité PM ↔ BE", "type": "select", "options": ["OK", "KO", "N/A"]},
            {"name": "lien_photos", "label": "Lien photos (Drive)", "type": "text", "ph": "https://drive.google.com/..."},
            {"name": "corps", "label": "Détail des BE (dictée 🎤)", "type": "textarea",
             "ph": "BE-06 : audit, préparation, 7 câbles clients, total 5 FO. BE-05 : ..."},
        ],
        "corps": (
            "Site : {site}.\n"
            "Tirage : {cable_tire}.\n"
            "{corps}\n"
            "Total soudures : {total_soudures} FO.\n"
            "Continuité {continuite} entre PM et BE.\n"
            "Photos : {lien_photos}"
        ),
    },
]

BY_KEY = {t["key"]: t for t in TEMPLATES}

# -- Moteur de rendu ----------------------------------------------------------

_PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def _val(values, k):
    v = values.get(k, "")
    return ("" if v is None else str(v)).strip()


def render_corps(corps_template, values):
    """Remplit le gabarit ; supprime toute ligne dont tous les champs sont vides."""
    out = []
    for line in corps_template.strip("\n").split("\n"):
        keys = _PLACEHOLDER.findall(line)
        if keys:
            if all(not _val(values, k) for k in keys):
                continue
            line = _PLACEHOLDER.sub(lambda m: _val(values, m.group(1)), line)
        out.append(line.rstrip())
    return "\n".join(out).strip()


def fr_date(iso):
    """YYYY-MM-DD -> DD/MM/YYYY (tolérant)."""
    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except Exception:
        return iso or ""


def signature():
    """Signature auto, paramétrable via l'env (SIGN_NAME / SIGN_PHONE)."""
    name = os.environ.get("SIGN_NAME", "").strip()
    phone = os.environ.get("SIGN_PHONE", "").strip()
    if not name and not phone:
        return ""
    line = name + (":" + phone if phone else "")
    return "Cordialement\n" + line


def _is_travaux(statut):
    return "travaux" in (statut or "").lower()


def build_cr(template, common, values):
    """Construit (sujet, corps) du compte-rendu au format réel terrain.

    Sujet = le code intervention (clé de tri boîte mail + Excel). Repli sur
    « label — date » si le code est vide.
    """
    equipe = (common.get("equipe") or "").strip()
    code = (common.get("code") or "").strip()
    statut = (common.get("statut") or "").strip()
    dpr = (common.get("dpr") or "").strip()

    lines = []
    if equipe:
        lines.append(equipe)
    if code:
        lines.append(code)
    if statut:
        lines.append(statut)
    if lines:
        lines.append("")

    lines.append(render_corps(template["corps"], values))

    consigne = (common.get("consigne") or "").strip()
    if consigne:
        if not consigne.endswith("."):
            consigne += "."
        lines += ["", "Consigne technicien suivant : " + consigne]

    # Bloc travaux : phrase + DPR
    if _is_travaux(statut):
        lines += ["", "Merci de passer la panne en travaux."]
        if dpr:
            lines.append("DPR : " + fr_date(dpr))
    elif dpr:
        lines += ["", "DPR : " + fr_date(dpr)]

    sig = signature()
    if sig:
        lines += ["", sig]

    body = "\n".join(lines).strip() + "\n"

    if code:
        subject = f"{code} — {statut}".rstrip(" —") if statut else code
    else:
        subject = f"{template['label']} — {fr_date(common.get('date_intervention',''))}".rstrip(" —")
    return subject, body
