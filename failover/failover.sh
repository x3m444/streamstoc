#!/usr/bin/env bash
set -a
source /home/ubuntu/streamstoc/.env
set +a

set -euo pipefail

PRIMARY_IP="${PRIMARY_IP:?PRIMARY_IP nesetat în .env}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:?DUCKDNS_TOKEN nesetat în .env}"
DUCKDNS_DOMAINS="${DUCKDNS_DOMAINS:-incercari}"

HEALTH_URL="https://${PRIMARY_HOSTNAME:-stoc.incercari.duckdns.org}/login/"
FAIL_THRESHOLD=3
RECOVER_THRESHOLD=3
CURL_TIMEOUT=8

STATE_FILE="/tmp/failover_state"
LOG_FILE="/var/log/failover.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

get_state() {
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        echo "PRIMARY_ACTIVE 0 0"
    fi
}

save_state() {
    echo "$1 $2 $3" > "$STATE_FILE"
}

check_primary() {
    curl -sf --max-time "$CURL_TIMEOUT" \
         --resolve "${PRIMARY_HOSTNAME:-stoc.incercari.duckdns.org}:443:${PRIMARY_IP}" \
         "$HEALTH_URL" -o /dev/null
}

update_duckdns() {
    local mode="$1"
    local ip
    if [[ "$mode" == "secondary" ]]; then
        ip=$(curl -sf --max-time 5 ifconfig.me)
    else
        ip=$(curl -sf --max-time 5 ifconfig.me)
    fi

    local result
    result=$(curl -sf --max-time 10 \
        "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAINS}&token=${DUCKDNS_TOKEN}&ip=${ip}")

    if [[ "$result" == "OK" ]]; then
        log "DuckDNS actualizat → $ip ($mode)"
        return 0
    else
        log "EROARE DuckDNS: răspuns=$result"
        return 1
    fi
}

notify() {
    local event="$1"
    local msg="$2"
    log "NOTIFICARE [$event]: $msg"
}

main() {
    read -r current_status fail_count recover_count < <(get_state)

    if check_primary; then
        if [[ "$current_status" == "SECONDARY_ACTIVE" ]]; then
            recover_count=$((recover_count + 1))
            log "Primar recuperat ($recover_count/$RECOVER_THRESHOLD)"

            if [[ "$recover_count" -ge "$RECOVER_THRESHOLD" ]]; then
                log "=== FAILBACK: reactivare server primar ==="
                if update_duckdns "primary"; then
                    notify "FAILBACK" "Primar online, DNS reîndreptat spre $PRIMARY_IP"
                    # Stop Docker services on secondary
                    cd /home/ubuntu/streamstoc
                    docker compose down
                    log "Docker services stopped pe secundar."
                    save_state "PRIMARY_ACTIVE" 0 0
                fi
            else
                save_state "SECONDARY_ACTIVE" 0 "$recover_count"
            fi
        else
            save_state "PRIMARY_ACTIVE" 0 0
        fi
    else
        fail_count=$((fail_count + 1))
        log "Primar indisponibil ($fail_count/$FAIL_THRESHOLD) — status: $current_status"

        if [[ "$current_status" == "PRIMARY_ACTIVE" ]]; then
            if [[ "$fail_count" -ge "$FAIL_THRESHOLD" ]]; then
                log "=== FAILOVER: activare server secundar ==="
                if update_duckdns "secondary"; then
                    notify "FAILOVER" "Primar căzut după $FAIL_THRESHOLD eșecuri. DNS → secundar"
                    # Auto-start Docker services on secondary
                    cd /home/ubuntu/streamstoc
                    docker compose up -d --remove-orphans
                    log "Docker services started pe secundar."
                    save_state "SECONDARY_ACTIVE" 0 0
                fi
            else
                save_state "PRIMARY_ACTIVE" "$fail_count" 0
            fi
        else
            save_state "SECONDARY_ACTIVE" "$fail_count" 0
        fi
    fi
}

main
