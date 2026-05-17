#!/usr/bin/env bash
# install-secondary.sh — configurare inițială server secundar
# Rulează o singură dată, cu sudo, pe serverul SECUNDAR

set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/stoc}"
SERVICE_USER="${SERVICE_USER:-ubuntu}"

echo "=== Configurare server secundar failover ==="

# 1. Clonăm/actualizăm repo-ul
if [[ -d "$REPO_DIR/.git" ]]; then
    echo "[1/6] Actualizare repo..."
    cd "$REPO_DIR" && git pull
else
    echo "[1/6] Clonare repo..."
    git clone "${GIT_REPO:?GIT_REPO nesetat}" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# 2. Copiem .env și îl completăm cu variabilele secundare
if [[ ! -f "$REPO_DIR/.env" ]]; then
    echo "[2/6] Creează $REPO_DIR/.env din exemplu și completează valorile!"
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    cp "$REPO_DIR/failover/.env.secondary.example" /tmp/env.secondary
    echo ""
    echo "  → Editează $REPO_DIR/.env și adaugă variabilele din /tmp/env.secondary"
    echo ""
fi

# 3. Drepturi pentru scripturi
echo "[3/6] Setare permisiuni..."
chmod +x "$REPO_DIR/failover/failover.sh"
chmod +x "$REPO_DIR/failover/sync-certs.sh"
mkdir -p /var/log
touch /var/log/failover.log
chown "$SERVICE_USER:$SERVICE_USER" /var/log/failover.log

# 4. Instalăm cron job pentru failover (la fiecare 30 secunde via două intrări cron)
echo "[4/6] Instalare cron job failover..."
CRON_CMD="cd $REPO_DIR && /usr/bin/env bash failover/failover.sh >> /var/log/failover.log 2>&1"
# Cron-ul are granularitate de 1 minut; rulăm de două ori cu 30s offset via sleep
CRON_LINE1="* * * * * $SERVICE_USER $CRON_CMD"
CRON_LINE2="* * * * * $SERVICE_USER sleep 30 && $CRON_CMD"

CRON_FILE="/etc/cron.d/stoc-failover"
cat > "$CRON_FILE" <<EOF
# Failover monitor — verifică primarul la fiecare ~30 secunde
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

$CRON_LINE1
$CRON_LINE2
EOF
chmod 644 "$CRON_FILE"

# 5. Verificăm că SSH merge spre primar
echo "[5/6] Verificare SSH spre primar..."
if [[ -n "${PRIMARY_IP:-}" ]]; then
    if ssh -o ConnectTimeout=5 -o BatchMode=yes \
           "${SERVICE_USER}@${PRIMARY_IP}" "echo ok" &>/dev/null; then
        echo "  → SSH spre primar OK"
    else
        echo "  → AVERTIZARE: SSH spre $PRIMARY_IP nu funcționează fără parolă."
        echo "     Asigură-te că cheia SSH e configurată corect între servere."
    fi
else
    echo "  → PRIMARY_IP nesetat, skip verificare SSH."
fi

# 6. Pornim stack-ul cu overlay pentru secundar
echo "[6/6] Pornire servicii Docker..."
cd "$REPO_DIR"
docker compose \
    -f docker-compose.yml \
    -f failover/docker-compose.secondary.yml \
    up -d --build --remove-orphans

echo ""
echo "=== Instalare completă ==="
echo ""
echo "Pași următori:"
echo "  1. Pe PRIMAR, adaugă în crontab:"
echo "     0 3 * * * cd $REPO_DIR && bash failover/sync-certs.sh"
echo "  2. Testează sync manual de pe primar: bash $REPO_DIR/failover/sync-certs.sh"
echo "  3. Testează failover manual: bash $REPO_DIR/failover/failover.sh"
echo "  4. Verifică loguri: tail -f /var/log/failover.log"
