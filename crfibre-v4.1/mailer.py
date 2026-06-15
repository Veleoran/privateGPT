# -*- coding: utf-8 -*-
"""
CR Fibre v4 — envoi mail texte brut.
Principal : Gmail SMTP (app password). Fallback : Brevo SMTP.
Aucune dépendance externe (smtplib stdlib couvre les deux relais).
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate


def _send_via(host, port, user, password, msg):
    with smtplib.SMTP(host, int(port), timeout=20) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(user, password)
        s.send_message(msg)


def send_cr(subject, body, to_addr, cc_addr=None):
    """Retourne (ok: bool, provider: str, error: str|None)."""
    from_name = os.environ.get("MAIL_FROM_NAME", "")
    from_addr = os.environ.get("MAIL_FROM_ADDR", os.environ.get("SMTP_USER", ""))

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_addr)) if from_name else from_addr
    msg["To"] = to_addr or ""
    if cc_addr:
        msg["Cc"] = cc_addr
    msg["Date"] = formatdate(localtime=True)

    recipients = [a for a in [to_addr] + ([cc_addr] if cc_addr else []) if a]
    if not recipients:
        return False, "aucun", "Aucun destinataire (MAIL_TO vide)"

    errors = []

    # 1) Gmail
    g = (
        os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        os.environ.get("SMTP_PORT", "587"),
        os.environ.get("SMTP_USER", ""),
        os.environ.get("SMTP_PASS", ""),
    )
    if g[2] and g[3]:
        try:
            _send_via(*g, msg)
            return True, "Gmail", None
        except Exception as e:
            errors.append(f"Gmail: {e}")

    # 2) Brevo fallback
    b = (
        os.environ.get("BREVO_HOST", "smtp-relay.brevo.com"),
        os.environ.get("BREVO_PORT", "587"),
        os.environ.get("BREVO_USER", ""),
        os.environ.get("BREVO_PASS", ""),
    )
    if b[2] and b[3]:
        try:
            _send_via(*b, msg)
            return True, "Brevo", None
        except Exception as e:
            errors.append(f"Brevo: {e}")

    return False, "aucun", " | ".join(errors) if errors else "Aucun relai configuré"
