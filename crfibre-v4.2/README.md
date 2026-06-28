# CR Fibre v4.2

App web auto-hébergée de comptes-rendus d'intervention FTTH.
Flask 3 + SQLite (WAL, stdlib) + mail texte brut (Gmail/Brevo) + export Excel + PWA.

## Nouveautés v4.2 — modèle calé sur le terrain réel
- **Code intervention** (ex. `C35536166-01`) : champ requis, présent partout — liste, ticket,
  **sujet du mail**, et surtout l'**Excel de paie**. C'est la clé du justificatif mensuel.
- **Format réel du CR** : le compte-rendu produit `équipe / code / statut → corps → DPR (si
  travaux) → signature` exactement comme les tickets terrain. Signature auto paramétrable
  (`SIGN_NAME` / `SIGN_PHONE`, défaut `Cordialement / Patrick Leal:0613359154`).
- **4 modèles** au lieu de 12 : `CR rapide` texte-libre dicté (défaut) + 3 accélérateurs
  (`Coupure/OTDR → Travaux`, `Reprise/jarretière → Clos`, `Gros chantier soudures`).
- **Statuts réels** : `Clos`, `Travaux`, `Clos/Travaux` (+ `En cours`, `Infructueuse`).
- **DPR** (date prochain RDV) : champ qui apparaît automatiquement pour les statuts Travaux.
- **Excel mensuel en 2 tableaux** : feuille **« À facturer »** (Clos + total points = la paie)
  et feuille **« Travaux »** à part (Code, Date, Type, DPR = suivi des reprises).
- **Pont Praxedo** : boutons **Copier** + **Partager** (partage Android natif) sur le ticket
  → coller le CR dans l'app Praxedo. Pas d'API requise (voir section Praxedo).
- **Migration auto** : la base existante est mise à jour sans perte (ajout colonnes `code`/`dpr`).
- Toujours **zéro dépendance ajoutée**, même port (8470 / 8447 Caddy).

## Praxedo — comment « augmenter les tickets » sans API
Praxedo a bien une API REST/SOAP, **mais elle exige un compte admin de l'entreprise** (OAuth 2.0
à configurer côté donneur d'ordre) — un technicien end-user n'y a pas accès, et il n'existe pas
d'email-to-ticket public. La voie réaliste **maintenant** : générer le CR ici, puis le **coller**
dans le formulaire Praxedo via le bouton **Copier** ou **Partager** (sélecteur Android). Si un jour
l'admin Praxedo fournit un accès API, on pourra ajouter un envoi direct (option future).

## Nouveautés v4.1
- **Dictée vocale terrain** : un micro 🎤 par champ texte / nombre / zone de texte. Web Speech API native (`fr-FR`), **zéro dépendance ajoutée**. Les nombres dictés sont normalisés (« moins vingt-deux virgule quatre » → `-22.4`). Dégradation propre : si le navigateur ne supporte pas, aucun micro n'apparaît et la saisie clavier reste 100 % fonctionnelle.
- **Copier le CR** : bouton sur la page ticket (coller dans un portail opérateur, SMS, etc.).
- Aucune nouvelle dépendance Python, aucun changement de schéma SQLite, aucun changement de port. Mise à jour = simple rebuild.

## Hérité de v4
- **Refacto propre** : code séparé (`app.py`, `crdata.py`, `db.py`, `mailer.py`, `export.py`), templates data-driven.
- **Scoring** : Seul = 1 pt, Binôme = 0,5 pt. Compteur points du mois sur l'accueil.
- **Export Excel** : semaine courante / mois courant / plage perso, avec ligne total points.
- **Mobile + PWA** : responsive, installable sur l'écran d'accueil Android (manifest + service worker). Pas d'app native, pas de Play Store.
- **Serveur waitress** (pur-python) au lieu du serveur de dev Flask.

## Dictée vocale — prérequis & privacy
- **Contexte sécurisé obligatoire** : la Web Speech API n'est activée qu'en HTTPS (ou `localhost`). Sur le Fairphone, passez par **Tailscale Serve** (`https://serveur.<tailnet>.ts.net`, certificat valide) — le micro est autorisé sans bidouille. Via Caddy `tls internal` (cert auto-signé), certains navigateurs bloquent le micro : préférez Tailscale Serve pour la voix.
- **Navigateur** : Chrome/Chromium Android (et navigateurs Chromium) supportent la reconnaissance. Firefox/LibreWolf ne l'implémentent pas → pas de micro affiché, saisie clavier inchangée.
- **Privacy** : sur Chrome, l'audio de dictée est transcrit côté Google (comme le clavier vocal Gboard). C'est le **seul** flux qui sort ; le CR, la base et le mail restent auto-hébergés. Le Fairphone terrain utilise déjà les services Google. Pour une dictée 100 % locale (hors scope v4.1), une piste future = Whisper/Vosk sur l'Acer ou via Ollama, exposé en interne uniquement.

## Arborescence
```
app.py crdata.py db.py mailer.py export.py
templates/  static/  Containerfile  crfibre.container  .env.example
```
Pour ajouter/modifier un type d'intervention : éditer `crdata.py` uniquement.

## Déploiement sur l'Acer (rootless Podman + Quadlet)

Depuis le PC, transférer puis se connecter :
```powershell
scp -i C:\Users\Leo Angelo\.ssh\id_ed25519_acer cr-fibre-v4.zip paul@192.168.2.2:~/
ssh -i C:\Users\Leo Angelo\.ssh\id_ed25519_acer paul@192.168.2.2
```

Sur l'Acer :
```bash
# 1. Extraire dans ~/crfibre (garde data/ si déjà existant)
mkdir -p ~/crfibre && cd ~/crfibre
unzip -o ~/cr-fibre-v4.zip
mkdir -p ~/crfibre/data

# 2. Config secrets
cp .env.example .env
nano .env        # renseigner SMTP_PASS, MAIL_TO, SECRET_KEY (cf. Vaultwarden)

# 3. Build image
podman build -t crfibre:latest .

# 4. Installer l'unité Quadlet
mkdir -p ~/.config/containers/systemd
cp crfibre.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start crfibre.service
systemctl --user status crfibre.service --no-pager

# 5. Vérifier
curl -s http://127.0.0.1:8470/sante      # {"status":"ok"}
```

`loginctl enable-linger paul` est déjà actif → le conteneur survit au reboot.

## Backup quotidien (cron)
```bash
sudo tee /etc/cron.daily/crfibre-backup >/dev/null <<'EOF'
#!/bin/sh
sqlite3 /home/paul/crfibre/data/crfibre.sqlite3 ".backup /home/paul/crfibre/backups/crfibre-$(date +%Y%m%d).sqlite3"
find /home/paul/crfibre/backups/ -name "*.sqlite3" -mtime +14 -delete
EOF
sudo chmod +x /etc/cron.daily/crfibre-backup
mkdir -p ~/crfibre/backups
```

## Accès LAN via Caddy (HTTPS)
Bloc à ajouter au Caddyfile (ex. port 8447) :
```
https://192.168.2.2:8447 {
    tls internal
    reverse_proxy 127.0.0.1:8470
}
```
Puis recharger Caddy. Le CA Caddy doit être importé dans le navigateur (Firefox/LibreWolf : Paramètres → Certificats → Autorités → Importer, cocher « confiance sites web »).

## Accès terrain via Tailscale Serve (HTTPS valide, sans bidouille cert)
```bash
tailscale serve --bg --https=443 http://127.0.0.1:8470
tailscale serve status
```
→ joignable sur `https://serveur.<ton-tailnet>.ts.net/` depuis le Fairphone (app Tailscale connectée), avec un certificat valide. Rien d'exposé sur Internet public.

## Mise à jour ultérieure
```bash
cd ~/crfibre && unzip -o ~/cr-fibre-vNEXT.zip
podman build -t crfibre:latest .
systemctl --user restart crfibre.service
```
La base `data/crfibre.sqlite3` n'est jamais écrasée (volume séparé).
