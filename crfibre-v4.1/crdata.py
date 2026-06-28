# -*- coding: utf-8 -*-
"""
CR Fibre v4 — Définition des templates d'intervention FTTH (data-driven).

Chaque template :
  key    : identifiant stable
  label  : libellé affiché
  fields : liste de champs {name, label, type, options?, required?, ph?}
  corps  : gabarit texte du CR. Chaque ligne contenant {placeholders}
           est supprimée si toutes ses valeurs sont vides.

Pour modifier/ajouter un template : éditer ce seul fichier. ~5 min.
"""
import re

OPERATEURS = ["Orange", "SFR", "Free", "Bouygues", "Autre"]

# -- Templates ----------------------------------------------------------------

TEMPLATES = [
    {
        "key": "be_signal",
        "label": "Contrôle signal au BE",
        "fields": [
            {"name": "ref_be", "label": "Réf BE / PBO", "type": "text", "required": True, "ph": "PBO-12"},
            {"name": "operateur", "label": "Opérateur", "type": "select", "options": OPERATEURS},
            {"name": "niveau_dbm", "label": "Niveau mesuré (dBm)", "type": "number", "ph": "-22.4"},
            {"name": "seuil", "label": "Conformité", "type": "select", "options": ["Conforme", "Hors seuil"]},
            {"name": "action", "label": "Action réalisée", "type": "textarea"},
        ],
        "corps": (
            "Contrôle signal au BE {ref_be} — opérateur {operateur}.\n"
            "Niveau mesuré : {niveau_dbm} dBm ({seuil}).\n"
            "{action}"
        ),
    },
    {
        "key": "pm_jarretiere",
        "label": "Jarretières / brassage PM",
        "fields": [
            {"name": "pm_ref", "label": "PM", "type": "text", "required": True, "ph": "PM-xxxxx"},
            {"name": "acces_pm", "label": "Accès PM", "type": "select", "options": ["Clé", "Badge", "Ouvert", "Code"]},
            {"name": "operateur", "label": "Opérateur", "type": "select", "options": OPERATEURS},
            {"name": "position_laser", "label": "Position (Baie/Tiroir/Module/Port)", "type": "text", "ph": "B2 T3 M4 P5"},
            {"name": "nb_jarretieres", "label": "Jarretières posées/reprises", "type": "number"},
            {"name": "e_intervention", "label": "e-intervention", "type": "select", "options": ["Validée", "Non validée", "N/A"]},
            {"name": "clients_up", "label": "Clients UP", "type": "text"},
        ],
        "corps": (
            "Brassage PM {pm_ref} (accès {acces_pm}) — opérateur {operateur}.\n"
            "Position : {position_laser}.\n"
            "Jarretières posées/reprises : {nb_jarretieres}.\n"
            "e-intervention : {e_intervention}.\n"
            "Clients UP : {clients_up}."
        ),
    },
    {
        "key": "soudures",
        "label": "Reprise de soudures",
        "fields": [
            {"name": "localisation", "label": "Localisation (Baie Tête Module)", "type": "text", "required": True, "ph": "B1 T2 M3"},
            {"name": "tube_bague", "label": "Tube / bague", "type": "text", "ph": "Orange-Bague"},
            {"name": "nb_pigtails", "label": "Pigtails remplacés", "type": "number"},
            {"name": "nb_fibres", "label": "Fibres soudées", "type": "number"},
            {"name": "remplacement", "label": "Type", "type": "select", "options": ["Avec remplacement", "Sans remplacement"]},
            {"name": "total_fibres", "label": "Total fibres", "type": "number"},
        ],
        "corps": (
            "Reprise de soudures — {localisation}.\n"
            "Tube / bague : {tube_bague}.\n"
            "Pigtails remplacés : {nb_pigtails}.\n"
            "Soudures : {nb_fibres} fibres ({remplacement}).\n"
            "Total soudures : {total_fibres} fibres."
        ),
    },
    {
        "key": "otdr",
        "label": "Recherche de panne OTDR",
        "fields": [
            {"name": "operateur", "label": "Opérateur", "type": "select", "options": OPERATEURS},
            {"name": "distance_m", "label": "Distance du défaut (m)", "type": "number", "required": True, "ph": "44"},
            {"name": "point_defaut", "label": "Point (PBO / PM-XX)", "type": "text", "ph": "PBO-07"},
            {"name": "nature", "label": "Nature", "type": "select",
             "options": ["Coupure", "Atténuation", "Vandalisme", "Tubes coupés à ras", "Connecteur défaut"]},
            {"name": "fibre_alt", "label": "Fibre alternative", "type": "text"},
            {"name": "localisation", "label": "Localisation (Baie Tête Module)", "type": "text"},
        ],
        "corps": (
            "Recherche de panne OTDR — opérateur {operateur}.\n"
            "Défaut localisé à {distance_m} m au {point_defaut}.\n"
            "Nature : {nature}.\n"
            "Fibre alternative : {fibre_alt}.\n"
            "Localisation : {localisation}."
        ),
    },
    {
        "key": "sav_signal",
        "label": "SAV signal dégradé",
        "fields": [
            {"name": "client", "label": "Client / PTO", "type": "text", "required": True},
            {"name": "operateur", "label": "Opérateur", "type": "select", "options": OPERATEURS},
            {"name": "niveau_avant", "label": "Niveau avant (dBm)", "type": "number"},
            {"name": "niveau_apres", "label": "Niveau après (dBm)", "type": "number"},
            {"name": "cause", "label": "Cause identifiée", "type": "text"},
            {"name": "action", "label": "Action", "type": "textarea"},
        ],
        "corps": (
            "SAV signal dégradé — {client}, opérateur {operateur}.\n"
            "Niveau avant : {niveau_avant} dBm — après : {niveau_apres} dBm.\n"
            "Cause : {cause}.\n"
            "{action}"
        ),
    },
    {
        "key": "vandalisme",
        "label": "Vandalisme → TRAVAUX",
        "fields": [
            {"name": "equipement", "label": "Équipement", "type": "select", "options": ["PBO", "PM"]},
            {"name": "ref", "label": "Référence", "type": "text", "required": True},
            {"name": "localisation", "label": "Localisation (Baie Tête Module)", "type": "text"},
            {"name": "constat", "label": "Constat vandalisme", "type": "textarea"},
            {"name": "pm_vandalise", "label": "PM vandalisé", "type": "select", "options": ["Oui", "Non"]},
        ],
        "corps": (
            "Constat vandalisme — {equipement} {ref}.\n"
            "Localisation : {localisation}.\n"
            "{constat}\n"
            "PM vandalisé : {pm_vandalise}."
        ),
    },
    {
        "key": "audit",
        "label": "Audit / diagnostic avant travaux",
        "fields": [
            {"name": "zone", "label": "Zone / PM / PBO", "type": "text", "required": True},
            {"name": "operateur", "label": "Opérateur", "type": "select", "options": OPERATEURS},
            {"name": "constat", "label": "Constat", "type": "textarea"},
            {"name": "recommandation", "label": "Recommandation", "type": "textarea"},
        ],
        "corps": (
            "Audit / diagnostic — {zone}.\n"
            "{constat}\n"
            "Recommandation : {recommandation}."
        ),
    },
    {
        "key": "expertise_rdv",
        "label": "Expertise / RDV tiers",
        "fields": [
            {"name": "tiers", "label": "Tiers / intervenant", "type": "text", "required": True},
            {"name": "objet", "label": "Objet du RDV", "type": "text"},
            {"name": "lieu", "label": "Lieu", "type": "text"},
            {"name": "compte_rendu", "label": "Compte-rendu", "type": "textarea"},
        ],
        "corps": (
            "Expertise / RDV avec {tiers}.\n"
            "Objet : {objet}.\n"
            "Lieu : {lieu}.\n"
            "{compte_rendu}"
        ),
    },
    {
        "key": "raccordement",
        "label": "Raccordement / reprise branchement",
        "fields": [
            {"name": "client", "label": "Client / PTO", "type": "text", "required": True},
            {"name": "operateur", "label": "Opérateur", "type": "select", "options": OPERATEURS},
            {"name": "type_intervention", "label": "Type", "type": "select",
             "options": ["Raccordement neuf", "Reprise branchement"]},
            {"name": "niveau_dbm", "label": "Niveau mesuré (dBm)", "type": "number"},
            {"name": "action", "label": "Détail", "type": "textarea"},
        ],
        "corps": (
            "{type_intervention} — {client}, opérateur {operateur}.\n"
            "Niveau mesuré : {niveau_dbm} dBm.\n"
            "{action}"
        ),
    },
    {
        "key": "recette",
        "label": "Mesure de validation / recette",
        "fields": [
            {"name": "ouvrage", "label": "Ouvrage / PM / PBO", "type": "text", "required": True},
            {"name": "nb_fibres", "label": "Fibres mesurées", "type": "number"},
            {"name": "resultat", "label": "Résultat", "type": "select",
             "options": ["Conforme", "Non conforme", "Conforme avec réserves"]},
            {"name": "reserves", "label": "Réserves", "type": "textarea"},
        ],
        "corps": (
            "Mesure de validation / recette — {ouvrage}.\n"
            "Fibres mesurées : {nb_fibres}.\n"
            "Résultat : {resultat}.\n"
            "Réserves : {reserves}."
        ),
    },
    {
        "key": "infructueuse",
        "label": "Intervention infructueuse",
        "fields": [
            {"name": "lieu", "label": "Lieu / client", "type": "text", "required": True},
            {"name": "motif", "label": "Motif", "type": "select",
             "options": ["Accès impossible", "Client absent", "Matériel manquant", "Hors périmètre", "Autre"]},
            {"name": "detail", "label": "Détail", "type": "textarea"},
        ],
        "corps": (
            "Intervention infructueuse — {lieu}.\n"
            "Motif : {motif}.\n"
            "{detail}"
        ),
    },
    {
        "key": "generique",
        "label": "Générique",
        "fields": [
            {"name": "objet", "label": "Objet", "type": "text", "required": True},
            {"name": "corps_libre", "label": "Compte-rendu", "type": "textarea"},
        ],
        "corps": "{objet}\n{corps_libre}",
    },
    # --- 2 slots libres éditables ---
    {
        "key": "libre1",
        "label": "Libre 1",
        "fields": [
            {"name": "objet", "label": "Objet", "type": "text", "required": True},
            {"name": "corps_libre", "label": "Compte-rendu", "type": "textarea"},
        ],
        "corps": "{objet}\n{corps_libre}",
    },
    {
        "key": "libre2",
        "label": "Libre 2",
        "fields": [
            {"name": "objet", "label": "Objet", "type": "text", "required": True},
            {"name": "corps_libre", "label": "Compte-rendu", "type": "textarea"},
        ],
        "corps": "{objet}\n{corps_libre}",
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


def status_line(statut, note=""):
    note = (note or "").strip()
    base = {
        "Clôturé": "Travaux clôturés.",
        "Passage en TRAVAUX": "Passage en TRAVAUX.",
        "Infructueuse": "Intervention infructueuse.",
    }.get(statut, "")
    if base and note:
        return base.rstrip(".") + " — " + note + "."
    return base


def build_cr(template, common, values):
    """Construit (sujet, corps) du compte-rendu en texte brut."""
    date_h = fr_date(common.get("date_intervention", ""))
    lines = [f"Intervention du {date_h}".rstrip()]
    equipe = (common.get("equipe") or "").strip()
    if equipe:
        lines.append("Équipe : " + equipe)
    lines.append("")
    lines.append(render_corps(template["corps"], values))

    consigne = (common.get("consigne") or "").strip()
    if consigne:
        if not consigne.endswith("."):
            consigne += "."
        lines += ["", "Consigne technicien suivant : " + consigne]

    sline = status_line(common.get("statut", ""), common.get("note_cloture", ""))
    if sline:
        lines += ["", sline]

    body = "\n".join(lines).strip() + "\n"
    subject = f"{template['label']} — {date_h}".rstrip(" —")
    return subject, body
