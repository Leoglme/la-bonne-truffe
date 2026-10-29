# Déploiement

La Bonne Truffe tourne sur le VPS, à côté de DevLeadHunter et avec la même mécanique : trois workflows GitHub Actions copient le code par SSH, systemd fait tourner l'API et le worker, pm2 le serveur Nuxt, et nginx termine le HTTPS avec les certificats Let's Encrypt créés par certbot.

## Ce qui tourne sur le VPS

| Quoi | Adresse publique | Sur le VPS |
|---|---|---|
| Dashboard Nuxt 4 (SSR) | https://la-bonne-truffe.dibodev.fr | pm2 `la-bonne-truffe.dibodev.fr` sur `127.0.0.1:5630`, lancé avec le `node` du shell interactif de `debian` : Nuxt 4 demande Node 20 ou plus, le démon pm2 tourne en Node 18 ; serveur Nitro dans `/var/www/la-bonne-truffe.dibodev.fr/server/`, fichiers publics dans `html/` |
| API FastAPI | https://api.la-bonne-truffe.dibodev.fr (documentation sur `/docs`) | service systemd `la-bonne-truffe-api`, uvicorn sur `127.0.0.1:8030` ; code et venv dans `/var/www/api.la-bonne-truffe.dibodev.fr/html/` |
| Worker de collecte | — | service systemd `la-bonne-truffe-worker` (`python worker.py`), même code et même venv que l'API |
| Base SQLite | — | `/var/www/api.la-bonne-truffe.dibodev.fr/data/la-bonne-truffe.db`, hors du dossier `api/` que chaque déploiement remplace |
| App Windows | Releases GitHub du dépôt | — |

Les ports 8030 et 5630 ne sont pris par aucun des projets déployés connus (DevLeadHunter : 8005 et 5615) ; l'étape 1 du premier déploiement le vérifie sur le VPS. Les www (`www.la-bonne-truffe.dibodev.fr`, `www.api.la-bonne-truffe.dibodev.fr`) sont couverts par les certificats ; celui du dashboard redirige vers le domaine nu, pour que la PWA n'ait qu'une origine.

## Les workflows

| Workflow | Quand | Ce qu'il fait |
|---|---|---|
| `deploy-api.yml` | Push sur `main` qui touche `api/`, pull request, ou à la main | ruff, mypy et pytest sous Python 3.11, celui de Debian 12 sur le VPS ; puis, sur `main` seulement : copie `api/`, met à jour le venv, écrit le `.env` depuis les secrets, lance `cli.py init-db` (migrations et seeders), installe et redémarre les deux services, vérifie `/api/v1/health` et que le worker tourne |
| `deploy-web.yml` | Push sur `main` qui touche `web/`, pull request, ou à la main | `npm run lint`, build Nitro avec `NUXT_PUBLIC_API_BASE=https://api.la-bonne-truffe.dibodev.fr` ; puis, sur `main` seulement : fichiers publics dans `html/`, serveur dans `server/`, redémarrage pm2, vérifie que l'accueil répond |
| `desktop-release.yml` | Push sur `main` qui touche `web/`, ou à la main | Installeur NSIS signé, publié en release GitHub `v0.1.<numéro de run>` avec le `latest.json` que l'app lit au démarrage |

Une pull request ne déploie jamais : elle ne lance que les contrôles. Un service qui ne répond pas après le redémarrage fait passer le déploiement au rouge, avec son statut et ses derniers logs.

## Secrets GitHub

À créer dans le dépôt (Settings → Secrets and variables → Actions) avant le premier déploiement : un secret manquant arrête le workflow avant qu'il touche au VPS.

| Secret | Valeur |
|---|---|
| `SSH_HOST`, `SSH_PORT`, `SSH_USERNAME`, `SSH_PRIVATE_KEY` | L'accès SSH du VPS, comme pour DevLeadHunter ; la clé privée peut être la sienne ou une clé dédiée ajoutée à `~/.ssh/authorized_keys` |
| `SECRET_KEY` | Clé de signature des JWT, aléatoire ; la changer déconnecte les sessions |
| `ADMIN_PASSWORD` | Le mot de passe du dashboard ; lu seulement à la création de l'utilisateur, le changer ensuite ne change pas celui de la base |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY_B64` | La paire Web Push ; en changer désabonne les appareils |
| `TAURI_UPDATER_PUBKEY`, `TAURI_SIGNING_PRIVATE_KEY`, `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | La clé de l'updater : clé publique, clé privée et son mot de passe ; la perdre oblige à réinstaller l'app à la main |
| `RESEND_API_KEY` | Facultatif : la clé Resend qui envoie le lien de « Mot de passe oublié » depuis `EMAIL_FROM` ; sans elle, l'API écrit le lien dans ses logs |

Avec `gh`, depuis la racine du dépôt, dans Git Bash. Les mots de passe sont lus par `read -s` : ils ne s'affichent pas et ne restent pas dans l'historique.

```bash
gh secret set SSH_HOST --body "IP_DU_VPS"
gh secret set SSH_PORT --body "PORT_SSH_DU_VPS"
gh secret set SSH_USERNAME --body "debian"
gh secret set SSH_PRIVATE_KEY < chemin/vers/la/cle/privee
read -rsp "Mot de passe du dashboard : " admin_password; echo; printf '%s' "$admin_password" | gh secret set ADMIN_PASSWORD; unset admin_password
python -c 'import secrets; print(secrets.token_urlsafe(48), end="")' | gh secret set SECRET_KEY
# tr retire les \r que Python ajoute sous Windows en écrivant dans un pipe.
(cd api && .venv/Scripts/python cli.py vapid-keys) | tr -d '\r' | gh secret set -f -
read -rsp "Mot de passe de la clé de mise à jour : " tauri_key_password; echo
mkdir -p ~/.tauri && (cd web && npx tauri signer generate -w ~/.tauri/la-bonne-truffe.key -p "$tauri_key_password")
printf '%s' "$tauri_key_password" | gh secret set TAURI_SIGNING_PRIVATE_KEY_PASSWORD; unset tauri_key_password
gh secret set TAURI_SIGNING_PRIVATE_KEY < ~/.tauri/la-bonne-truffe.key
gh secret set TAURI_UPDATER_PUBKEY < ~/.tauri/la-bonne-truffe.key.pub
read -rsp "Clé Resend : " resend_api_key; echo; printf '%s' "$resend_api_key" | gh secret set RESEND_API_KEY; unset resend_api_key
```

Les adresses (`API_BASE_URL`, `WEB_BASE_URL`, `CORS_ORIGINS`), `DATABASE_URL`, `COLLECT_SKIPPED_SOURCES` et l'adresse `contact@dibodev.fr` (`ADMIN_EMAIL`, `VAPID_SUBJECT`, User-Agent) ne sont pas secrètes : elles sont écrites dans `deploy-api.yml`. L'inscription reste ouverte, comme le veut `SIGNUP_ENABLED` par défaut : pour la fermer, ajouter `SIGNUP_ENABLED=false` au `.env` qu'écrit `deploy-api.yml`.

## Nginx

Les deux confs sont dans `deploy/nginx/`. Elles remplacent celles que certbot a créées, avec les mêmes certificats, et suivent celles de DevLeadHunter : `/_nuxt/` servi par nginx et le reste par Nitro pour le dashboard, un proxy vers uvicorn pour l'API (avec 300 s de délai de lecture pour un relevé lancé à la main). Les workflows ne touchent pas à nginx : une conf se change dans le dépôt, puis sur le VPS, une fois sur `main` :

```bash
for site in la-bonne-truffe.dibodev.fr api.la-bonne-truffe.dibodev.fr; do sudo curl -fsSL -o "/etc/nginx/sites-available/$site" "https://raw.githubusercontent.com/Leoglme/la-bonne-truffe/main/deploy/nginx/$site.conf" && sudo ln -sf "/etc/nginx/sites-available/$site" "/etc/nginx/sites-enabled/$site"; done
sudo nginx -t && sudo systemctl reload nginx
```

Si `nginx -t` signale une erreur, ne pas recharger : nginx continue de servir l'ancienne conf tant qu'il n'est pas rechargé.

## Premier déploiement

1. Sur le VPS, vérifier que les ports sont libres : `sudo ss -ltnp | grep -E ':(8030|5630) '` ne doit rien afficher.
2. Créer les secrets.
3. Merger sur `main` : `deploy-api` et `deploy-web` déploient, `desktop-release` publie la première release.
4. Poser les confs nginx.
5. Ouvrir https://la-bonne-truffe.dibodev.fr et se connecter avec `contact@dibodev.fr` et `ADMIN_PASSWORD`. Sur l'iPhone et l'iPad : Safari, Partager, « Sur l'écran d'accueil », puis Réglages → Notifications dans l'app.
6. Installer l'app Windows depuis la dernière release sur chaque PC, et s'y connecter : elle démarre ensuite avec Windows, cachée dans la zone de notification, et relaie la Centrale Canine. Les versions suivantes arrivent par la mise à jour intégrée.

## Au quotidien

| Pour | Sur le VPS |
|---|---|
| Suivre l'API | `sudo journalctl -u la-bonne-truffe-api -f` |
| Suivre le worker | `sudo journalctl -u la-bonne-truffe-worker -f` |
| Suivre le dashboard | `pm2 logs la-bonne-truffe.dibodev.fr` |
| Redémarrer | `sudo systemctl restart la-bonne-truffe-api la-bonne-truffe-worker`, `pm2 restart la-bonne-truffe.dibodev.fr` |
| Lancer une commande de `cli.py` | `cd /var/www/api.la-bonne-truffe.dibodev.fr/html/api && ../.venv/bin/python cli.py push-test` |

## La collecte

Le worker du VPS relève Chiens de France, Chiots de France, Whoof et Cœur de Cocker avec le `curl` de Debian et le User-Agent honnête (`02-sources.md`). Whoof et Cœur de Cocker, ajoutés le 29/10/2026, n'ont été essayés que depuis un PC : leur pastille dans Sources dira au premier relevé si le VPS passe. Il ne relève pas la Centrale Canine : `deploy-api.yml` écrit `COLLECT_SKIPPED_SOURCES=centrale_canine` dans le `.env`, parce que Cloudflare refuse les adresses de serveur et le `curl` de Linux (`02-sources.md`).

La Centrale Canine est relayée par l'app Windows des PC où elle est installée et connectée :
- l'app démarre avec Windows, cachée dans la zone de notification, et vérifie toutes les 5 minutes si le relevé de l'heure est dû ;
- le premier PC qui le demande le fait : il lit les pages que l'API lui donne avec le `curl.exe` de Windows, sans fenêtre, et les renvoie à l'API, qui fait le relevé habituel ; l'autre PC passe son tour ;
- quand aucun PC n'est allumé, ses portées attendent le prochain démarrage, et les autres sources continuent sans elle ;
- la page Sources l'affiche « Relevée par l'app Windows » ; dans l'app Windows, « Relever maintenant » relaie tout de suite, et sur le web ou le téléphone, « Demander un relevé » le fait faire par un PC allumé dans les 5 minutes.

Un relais envoie environ 1 Mo de pages : la conf nginx de l'API accepte 10 Mo par requête (`client_max_body_size`).
