# -*- coding: utf-8 -*-
"""
CR Fibre v4.1 — application Flask (mono-utilisateur, auto-hébergée).
Backend Flask + Jinja2 + SQLite WAL. Mail texte brut (Gmail/Brevo).
Scoring : Seul = 1 pt, Binôme = 0,5 pt. Export Excel hebdo/mensuel. PWA.
v4.1 : dictée vocale terrain (Web Speech API, fr-FR) + copie du CR. Zéro dépendance ajoutée.
"""
import os
import json
import datetime as dt

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, abort, send_file, jsonify, Response,
)

import crdata
import db
import mailer
import export

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me")

STATUTS = ["En cours", "Clôturé", "Passage en TRAVAUX", "Infructueuse"]
EFFECTIFS = ["Seul", "Binôme"]
POINTS = {"Seul": 1.0, "Binôme": 0.5}

with app.app_context():
    db.init_db()


# -- Pages --------------------------------------------------------------------

@app.route("/")
def index():
    rows = db.list_recent(50)
    start, end = export.current_month()
    pts, nb = db.sum_points(start, end)
    return render_template("index.html", rows=rows, mois_points=pts, mois_nb=nb)


@app.route("/nouveau")
def choisir():
    return render_template("choisir.html", templates=crdata.TEMPLATES)


@app.route("/nouveau/<key>", methods=["GET", "POST"])
def nouveau(key):
    tpl = crdata.BY_KEY.get(key)
    if not tpl:
        abort(404)

    if request.method == "POST":
        # champs communs
        common = {
            "date_intervention": request.form.get("date_intervention", ""),
            "equipe": request.form.get("equipe", "").strip(),
            "effectif": request.form.get("effectif", "Seul"),
            "statut": request.form.get("statut", "En cours"),
            "consigne": request.form.get("consigne", "").strip(),
            "note_cloture": request.form.get("note_cloture", "").strip(),
        }
        # champs du template
        values = {f["name"]: request.form.get(f["name"], "").strip() for f in tpl["fields"]}

        subject, body = crdata.build_cr(tpl, common, values)
        points = POINTS.get(common["effectif"], 1.0)

        rec = {
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "date_intervention": common["date_intervention"],
            "template_key": tpl["key"],
            "template_label": tpl["label"],
            "equipe": common["equipe"],
            "effectif": common["effectif"],
            "points": points,
            "statut": common["statut"],
            "consigne": common["consigne"],
            "fields_json": json.dumps(values, ensure_ascii=False),
            "corps": body,
            "mail_envoye": 0,
            "mail_provider": None,
            "destinataires": None,
        }
        iid = db.insert_intervention(rec)

        # mail déclenché pour tout statut sauf "En cours"
        if common["statut"] != "En cours":
            to = os.environ.get("MAIL_TO", "")
            cc = os.environ.get("MAIL_CC", "") or None
            ok, provider, err = mailer.send_cr(subject, body, to, cc)
            dest = ", ".join([a for a in [to, cc] if a])
            db.update_mail_status(iid, ok, provider, dest if ok else None)
            if ok:
                flash(f"CR enregistré et envoyé via {provider}.", "ok")
            else:
                flash(f"CR enregistré mais mail NON envoyé : {err}", "err")
        else:
            flash("CR enregistré (statut En cours — pas de mail).", "ok")

        return redirect(url_for("ticket", iid=iid))

    today = dt.date.today().isoformat()
    return render_template(
        "form.html", tpl=tpl, statuts=STATUTS, effectifs=EFFECTIFS,
        points=POINTS, today=today,
    )


@app.route("/ticket/<int:iid>")
def ticket(iid):
    row = db.get(iid)
    if not row:
        abort(404)
    fields = json.loads(row["fields_json"] or "{}")
    return render_template("ticket.html", t=row, fields=fields)


@app.route("/ticket/<int:iid>/renvoyer", methods=["POST"])
def renvoyer(iid):
    row = db.get(iid)
    if not row:
        abort(404)
    subject = f"{row['template_label']} — {crdata.fr_date(row['date_intervention'] or '')}".rstrip(" —")
    to = os.environ.get("MAIL_TO", "")
    cc = os.environ.get("MAIL_CC", "") or None
    ok, provider, err = mailer.send_cr(subject, row["corps"], to, cc)
    dest = ", ".join([a for a in [to, cc] if a])
    db.update_mail_status(iid, ok, provider, dest if ok else None)
    flash(f"Renvoyé via {provider}." if ok else f"Échec renvoi : {err}", "ok" if ok else "err")
    return redirect(url_for("ticket", iid=iid))


@app.route("/export")
def export_page():
    ws, we = export.current_week()
    ms, me = export.current_month()
    wpts, wnb = db.sum_points(ws, we)
    mpts, mnb = db.sum_points(ms, me)
    return render_template(
        "export.html",
        week=(ws, we, wpts, wnb), month=(ms, me, mpts, mnb),
        today=dt.date.today().isoformat(),
    )


@app.route("/export.xlsx")
def export_xlsx():
    period = request.args.get("period", "month")
    if period == "week":
        start, end = export.current_week()
    elif period == "month":
        start, end = export.current_month()
    else:  # custom
        start = request.args.get("start") or dt.date.today().replace(day=1).isoformat()
        end = request.args.get("end") or dt.date.today().isoformat()
    bio, fname = export.build_xlsx(start, end)
    return send_file(
        bio, as_attachment=True, download_name=fname,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# -- PWA / santé --------------------------------------------------------------

@app.route("/sante")
def sante():
    return jsonify(status="ok")


@app.route("/manifest.webmanifest")
def manifest():
    return app.send_static_file("manifest.webmanifest")


@app.route("/sw.js")
def sw():
    # servi à la racine pour couvrir tout le scope
    resp = app.send_static_file("sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


if __name__ == "__main__":
    port = int(os.environ.get("CRFIBRE_PORT", "8470"))
    app.run(host="0.0.0.0", port=port)
