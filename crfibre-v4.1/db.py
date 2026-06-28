# -*- coding: utf-8 -*-
"""CR Fibre v4 — couche SQLite stdlib en mode WAL (mono-écrivain, zéro ORM)."""
import os
import sqlite3
import json

DB_PATH = os.environ.get("CRFIBRE_DB", os.path.join(os.path.dirname(__file__), "data", "crfibre.sqlite3"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS interventions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at        TEXT NOT NULL,
    date_intervention TEXT,
    template_key      TEXT NOT NULL,
    template_label    TEXT,
    equipe            TEXT,
    effectif          TEXT,     -- 'Seul' | 'Binôme'
    points            REAL,     -- 1.0 | 0.5
    statut            TEXT,
    consigne          TEXT,
    fields_json       TEXT,
    corps             TEXT,
    mail_envoye       INTEGER DEFAULT 0,
    mail_provider     TEXT,
    destinataires     TEXT
);
CREATE INDEX IF NOT EXISTS idx_date ON interventions(date_intervention);
CREATE INDEX IF NOT EXISTS idx_created ON interventions(created_at);
"""


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def init_db():
    con = connect()
    con.executescript(SCHEMA)
    con.commit()
    con.close()


def insert_intervention(d):
    con = connect()
    cur = con.execute(
        """INSERT INTO interventions
           (created_at, date_intervention, template_key, template_label, equipe,
            effectif, points, statut, consigne, fields_json, corps,
            mail_envoye, mail_provider, destinataires)
           VALUES (:created_at, :date_intervention, :template_key, :template_label, :equipe,
            :effectif, :points, :statut, :consigne, :fields_json, :corps,
            :mail_envoye, :mail_provider, :destinataires)""",
        d,
    )
    con.commit()
    new_id = cur.lastrowid
    con.close()
    return new_id


def update_mail_status(iid, sent, provider, destinataires):
    con = connect()
    con.execute(
        "UPDATE interventions SET mail_envoye=?, mail_provider=?, destinataires=? WHERE id=?",
        (1 if sent else 0, provider, destinataires, iid),
    )
    con.commit()
    con.close()


def get(iid):
    con = connect()
    row = con.execute("SELECT * FROM interventions WHERE id=?", (iid,)).fetchone()
    con.close()
    return row


def list_recent(limit=50):
    con = connect()
    rows = con.execute(
        "SELECT * FROM interventions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return rows


def _range(start, end):
    """Sélection par date_intervention si présente, sinon created_at. Bornes incluses."""
    con = connect()
    rows = con.execute(
        """SELECT * FROM interventions
           WHERE COALESCE(NULLIF(date_intervention,''), substr(created_at,1,10))
                 BETWEEN ? AND ?
           ORDER BY COALESCE(NULLIF(date_intervention,''), substr(created_at,1,10)) ASC, id ASC""",
        (start, end),
    ).fetchall()
    con.close()
    return rows


def list_period(start, end):
    return _range(start, end)


def sum_points(start, end):
    rows = _range(start, end)
    return round(sum((r["points"] or 0) for r in rows), 2), len(rows)
