#!/usr/bin/env bash
# sync-certs.sh — sincronizează acme.json de pe PRIMAR pe SECUNDAR
# Rulează pe PRIMAR via cron: 0 3 * * * /opt/stoc/failover/sync-certs.sh
#
# Necesar pentru ca secundarul să aibă certificate SSL valide fără
# să facă un nou DNS challenge (care ar dura 1-2 minute la failover).

set -euo pipefail

SECONDARY_HOST="${SECONDARY_HOST:?SECONDARY_HOST nesetat în .env}"
SECONDARY_USER="${SECONDARY_USER:-ubuntu}"
REMOTE_PATH="${REMOTE_PATH:-/opt/stoc/letsencrypt}"
LOCAL_ACME="$(dirname "$(dirname "$(realpath "$0")")")/letsencrypt/acme.json"
LOG_FILE="/var/log/cert-sync.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

if [[ ! -f "$LOCAL_ACME" ]]; then
    log "EROARE: acme.json nu există la $LOCAL_ACME"
    exit 1
fi

CERT_COUNT=$(python3 -c "
import json
try:
    d = json.load(open('$LOCAL_ACME'))
    print(len(d.get('myresolver', {}).get('Certificates', [])))
except: print(0)
" 2>/dev/null || echo "0")

if [[ "$CERT_COUNT" -eq 0 ]]; then
    log "AVERTIZARE: acme.json pare gol ($CERT_COUNT certificate). Skip sync."
    exit 0
fi

log "Sincronizare $CERT_COUNT certificate → $SECONDARY_HOST..."

rsync -az --chmod=F600 \
    -e "ssh -o ConnectTimeout=10" \
    "$LOCAL_ACME" \
    "${SECONDARY_USER}@${SECONDARY_HOST}:${REMOTE_PATH}/acme.json"

if [[ $? -eq 0 ]]; then
    log "OK → $SECONDARY_HOST:$REMOTE_PATH/acme.json"
    ssh -o ConnectTimeout=10 "${SECONDARY_USER}@${SECONDARY_HOST}" \
        "docker kill --signal=SIGUSR1 traefik 2>/dev/null || true"
    log "Traefik pe secundar reîncărcat."
else
    log "EROARE: rsync eșuat!"
    exit 1
fi
