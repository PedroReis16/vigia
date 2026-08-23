#!/bin/bash
# ─── CORES ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✔]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✘]${NC} $1"; exit 1; }

# ─── DIRETÓRIO BASE ───────────────────────────────────────────────────────────
BASE_DIR=$(pwd)

# ─── DOMÍNIOS (Cloudflare) ────────────────────────────────────────────────────
SERVICES_DOMAIN="services.vigiadeteccoes.com.br"
INGEST_DOMAIN="ingest.vigiadeteccoes.com.br"
MQTT_DOMAIN="mqtt.vigiadeteccoes.com.br"   # CONFIRME: assumido seguindo o padrão do ingest, DNS-only na Cloudflare
# CONFIRME: não foi especificado no domínio base — assumi o mesmo padrão de "services".
# Se for outro, troque aqui (ex: se preferir path-based sob SERVICES_DOMAIN).
PORTAINER_DOMAIN="portainer.vigiadeteccoes.com.br"

# ─── SEGREDOS (.env, NÃO versionado no Git) ───────────────────────────────────
# O .env deve conter, no mínimo:
#   CLOUDFLARE_DNS_API_TOKEN=<token Cloudflare com Zone:Read + DNS:Edit>
#   (aliases aceitos: CF_DNS_API_TOKEN ou DNS_API_TOKEN)
#   MOSQUITTO_IOTAGENT_PASSWORD=...
#   MOSQUITTO_DEVICE_PASSWORD=...
if [ ! -f "$BASE_DIR/.env" ]; then
  err "Arquivo .env não encontrado em $BASE_DIR. Crie com: CLOUDFLARE_DNS_API_TOKEN=<seu_token>"
fi
set -a
source "$BASE_DIR/.env"
set +a

# Normaliza o nome que o provider ACME do Traefik (lego) realmente lê.
CLOUDFLARE_DNS_API_TOKEN="${CLOUDFLARE_DNS_API_TOKEN:-${CF_DNS_API_TOKEN:-${DNS_API_TOKEN:-}}}"
[ -z "$CLOUDFLARE_DNS_API_TOKEN" ] && err "CLOUDFLARE_DNS_API_TOKEN não definido no .env"
[ -z "$MOSQUITTO_IOTAGENT_PASSWORD" ] && err "MOSQUITTO_IOTAGENT_PASSWORD não definido no .env"
[ -z "$MOSQUITTO_DEVICE_PASSWORD" ] && err "MOSQUITTO_DEVICE_PASSWORD não definido no .env"

# ─── REDE ─────────────────────────────────────────────────────────────────────
log "Criando rede vigia-network..."
docker network inspect vigia-network &>/dev/null || docker network create vigia-network
log "Rede vigia-network pronta."

# ─── REDIS ────────────────────────────────────────────────────────────────────
log "Subindo Redis..."
docker run -d \
  --name vigia-redis \
  --hostname redis \
  --network-alias redis \
  --restart unless-stopped \
  --network vigia-network \
  -p 6379:6379 \
  redis:latest
log "Redis OK."

# ─── POSTGRES ─────────────────────────────────────────────────────────────────
log "Subindo Postgres..."
docker run -d \
  --name vigia-postgres \
  --hostname postgres \
  --network-alias postgres \
  --restart unless-stopped \
  --network vigia-network \
  -p 5432:5432 \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin123 \
  -e POSTGRES_DB=vigia \
  postgres:15
log "Postgres OK."

# ─── MINIO ────────────────────────────────────────────────────────────────────
log "Subindo Minio..."
mkdir -p "$BASE_DIR/minio_data"
docker run -d \
  --name minio \
  --restart always \
  --network vigia-network \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=password123 \
  -e MINIO_BROWSER_REDIRECT_URL=https://${SERVICES_DOMAIN}/bucket \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.minio-console.rule=Host(\`${SERVICES_DOMAIN}\`) && PathPrefix(\`/bucket\`)" \
  --label "traefik.http.routers.minio-console.entrypoints=websecure" \
  --label "traefik.http.routers.minio-console.tls=true" \
  --label "traefik.http.routers.minio-console.tls.certresolver=letsencrypt" \
  --label "traefik.http.routers.minio-console.middlewares=strip-bucket" \
  --label "traefik.http.middlewares.strip-bucket.stripprefix.prefixes=/bucket" \
  --label "traefik.http.services.minio-console.loadbalancer.server.port=9001" \
  -v "$BASE_DIR/minio_data":/data \
  quay.io/minio/minio:latest \
  server --console-address ":9001" /data
log "Minio OK."

# ─── MEDIAMTX ─────────────────────────────────────────────────────────────────
# Imagem custom (Alpine + curl/jq) para hooks runOnUnread — NÃO buildar na VM.
# Override no .env: MEDIAMTX_IMAGE=usuario/vigia-mediamtx:tag
MEDIAMTX_IMAGE="${MEDIAMTX_IMAGE:-pedroreis16/vigia-mediamtx:latest}"
MEDIAMTX_HOOK="$BASE_DIR/mediamtx-hooks/on_unread_stop_streaming.sh"
MEDIAMTX_CONF="$BASE_DIR/mediamtx/mediamtx.yml"

log "Preparando config do MediaMTX..."
mkdir -p "$BASE_DIR/mediamtx" "$BASE_DIR/mediamtx-hooks"

# Bind de arquivo inexistente vira diretório no Docker — limpa estado quebrado.
if [ -d "$MEDIAMTX_CONF" ]; then
  warn "Removendo mediamtx.yml inválido (era diretório)..."
  rm -rf "$MEDIAMTX_CONF"
fi
if [ -d "$MEDIAMTX_HOOK" ]; then
  warn "Removendo hook inválido (era diretório)..."
  rm -rf "$MEDIAMTX_HOOK"
fi

[ -f "$MEDIAMTX_CONF" ] || err "Arquivo ausente: $MEDIAMTX_CONF (copie deploy/mediamtx/mediamtx.yml para a VM)"
[ -f "$MEDIAMTX_HOOK" ] || err "Arquivo ausente: $MEDIAMTX_HOOK (copie deploy/mediamtx-hooks/on_unread_stop_streaming.sh para a VM)"
chmod +x "$MEDIAMTX_HOOK"

log "Baixando imagem MediaMTX ($MEDIAMTX_IMAGE)..."
docker pull "$MEDIAMTX_IMAGE"

log "Subindo MediaMTX..."
docker run -d \
  --name vigia-mediamtx \
  --restart unless-stopped \
  --network vigia-network \
  -e VIGIA_API_BASE=http://vigia-api:8080 \
  -e VIGIA_MEDIAMTX_TOKEN="${VIGIA_MEDIAMTX_TOKEN:-CHANGE_ME_MEDIAMTX_WEBHOOK_TOKEN}" \
  -e UNDEMAND_GRACE_SECONDS=3 \
  -p 1935:1935 \
  -p 8189:8189/udp \
  -p 8189:8189/tcp \
  -p 8888:8888 \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.mediamtx-play.rule=Host(\`${SERVICES_DOMAIN}\`) && PathPrefix(\`/live\`)" \
  --label "traefik.http.routers.mediamtx-play.entrypoints=websecure" \
  --label "traefik.http.routers.mediamtx-play.tls=true" \
  --label "traefik.http.routers.mediamtx-play.tls.certresolver=letsencrypt" \
  --label "traefik.http.routers.mediamtx-play.priority=100" \
  --label "traefik.http.services.mediamtx-play.loadbalancer.server.port=8889" \
  --label "traefik.tcp.routers.mediamtx-ingest.rule=HostSNI(\`${INGEST_DOMAIN}\`)" \
  --label "traefik.tcp.routers.mediamtx-ingest.entrypoints=ingest" \
  --label "traefik.tcp.routers.mediamtx-ingest.tls=true" \
  --label "traefik.tcp.routers.mediamtx-ingest.tls.certresolver=letsencrypt" \
  --label "traefik.tcp.services.mediamtx-ingest.loadbalancer.server.port=1935" \
  -v "$MEDIAMTX_CONF":/mediamtx.yml:ro \
  -v "$MEDIAMTX_HOOK":/hooks/on_unread_stop_streaming.sh:ro \
  "$MEDIAMTX_IMAGE"
log "MediaMTX OK."

# ─── TRAEFIK ──────────────────────────────────────────────────────────────────
log "Subindo Traefik..."
# CLOUDFLARE_DNS_API_TOKEN é exigido pelo dnsChallenge provider=cloudflare (lego).
# Token Cloudflare: Zone → Read + DNS → Edit na zona vigiadeteccoes.com.br.
mkdir -p "$BASE_DIR/certificates"
touch "$BASE_DIR/certificates/acme.json"
chmod 600 "$BASE_DIR/certificates/acme.json"

docker run -d \
  --name traefik \
  --restart always \
  --network vigia-network \
  -e CLOUDFLARE_DNS_API_TOKEN="${CLOUDFLARE_DNS_API_TOKEN}" \
  -p 80:80 \
  -p 443:443 \
  -p 8443:8443 \
  -p 8883:8883 \
  -p 1883:1883 \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v "$BASE_DIR/traefik/traefik.yml":/etc/traefik/traefik.yml:ro \
  -v "$BASE_DIR/traefik/dynamic.yml":/etc/traefik/dynamic.yml:ro \
  -v "$BASE_DIR/certificates":/certificates \
  traefik:v3.6 \
  --configFile=/etc/traefik/traefik.yml
log "Traefik OK."

# ─── PORTAINER ────────────────────────────────────────────────────────────────
log "Subindo Portainer..."
docker run -d \
  --name portainer \
  --restart unless-stopped \
  --network vigia-network \
  --security-opt no-new-privileges:true \
  -v /etc/localtime:/etc/localtime:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v portainer_data:/data \
  -v /home/ubuntu:/home/ubuntu:ro \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.portainer.rule=Host(\`${PORTAINER_DOMAIN}\`)" \
  --label "traefik.http.routers.portainer.entrypoints=websecure" \
  --label "traefik.http.routers.portainer.tls=true" \
  --label "traefik.http.routers.portainer.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.portainer.loadbalancer.server.port=9000" \
  portainer/portainer-ce:latest
log "Portainer OK."

# ─── FIWARE: MONGO HISTÓRICO ──────────────────────────────────────────────────
log "Subindo Mongo Histórico..."
docker run -d \
  --name fiware-mongo-historical \
  --hostname mongo-db-historical \
  --restart always \
  --network vigia-network \
  -p 27077:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin123 \
  -v mongo-historical-data:/data/db \
  mongo:6.0 \
  mongod --nojournal --auth
log "Mongo Histórico OK."

# ─── FIWARE: MONGO INTERNO ────────────────────────────────────────────────────
log "Subindo Mongo Interno..."
docker run -d \
  --name fiware-mongo-internal \
  --hostname mongo-db-internal \
  --restart always \
  --network vigia-network \
  -p 27067:27017 \
  -v mongo-internal-data:/data/db \
  mongo:6.0 \
  mongod --nojournal
log "Mongo Interno OK."

# ─── AGUARDA MONGOS ───────────────────────────────────────────────────────────
warn "Aguardando Mongos iniciarem (15s)..."
sleep 15

# ─── FIWARE: ORION ────────────────────────────────────────────────────────────
log "Subindo Orion..."
docker run -d \
  --name fiware-orion \
  --hostname orion \
  --restart always \
  --network vigia-network \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.orion.rule=Host(\`${SERVICES_DOMAIN}\`) && PathPrefix(\`/vigia/fiware/orion\`)" \
  --label "traefik.http.routers.orion.entrypoints=websecure" \
  --label "traefik.http.routers.orion.tls=true" \
  --label "traefik.http.routers.orion.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.orion.loadbalancer.server.port=1026" \
  --label "traefik.http.routers.orion.middlewares=strip-orion,cors@file" \
  --label "traefik.http.middlewares.strip-orion.stripprefix.prefixes=/vigia/fiware/orion" \
  fiware/orion:3.11.0 \
  -dbhost mongo-db-historical \
  -dbuser admin \
  -dbpwd admin123 \
  -dbAuthDb admin \
  -corsOrigin __ALL \
  -corsMaxAge 600
log "Orion OK."

# ─── FIWARE: MOSQUITTO ────────────────────────────────────────────────────────
log "Preparando config do Mosquitto..."
mkdir -p "$BASE_DIR/mosquitto"
# Se uma tentativa anterior criou mosquitto.conf como diretório, remove
if [ -d "$BASE_DIR/mosquitto/mosquitto.conf" ]; then
  warn "Removendo mosquitto.conf inválido (era diretório)..."
  rm -rf "$BASE_DIR/mosquitto/mosquitto.conf"
fi
# Garante o arquivo de config (não depende de cópia manual no servidor)
cat > "$BASE_DIR/mosquitto/mosquitto.conf" <<'EOF'
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwordfile
listener 9001
protocol websockets
allow_anonymous true
EOF
# Sanity check: tem que ser arquivo, senão o Docker recria como pasta
[ -f "$BASE_DIR/mosquitto/mosquitto.conf" ] || err "mosquitto.conf não é um arquivo em $BASE_DIR/mosquitto/"

log "Gerando passwordfile do Mosquitto..."
if [ -d "$BASE_DIR/mosquitto/passwordfile" ]; then
  warn "Removendo passwordfile inválido (era diretório)..."
  rm -rf "$BASE_DIR/mosquitto/passwordfile"
fi
docker run --rm -v "$BASE_DIR/mosquitto":/mosquitto/config eclipse-mosquitto:latest \
  mosquitto_passwd -b -c /mosquitto/config/passwordfile iotagent "$MOSQUITTO_IOTAGENT_PASSWORD"
docker run --rm -v "$BASE_DIR/mosquitto":/mosquitto/config eclipse-mosquitto:latest \
  mosquitto_passwd -b /mosquitto/config/passwordfile vigia-device "$MOSQUITTO_DEVICE_PASSWORD"
[ -f "$BASE_DIR/mosquitto/passwordfile" ] || err "passwordfile não foi gerado como arquivo"

# eclipse-mosquitto roda como UID/GID 1883 — sem isso o broker não abre o pwfile.
log "Ajustando permissões do Mosquitto (UID 1883)..."
docker run --rm -v "$BASE_DIR/mosquitto":/mosquitto/config alpine:3.21 \
  sh -c 'chown -R 1883:1883 /mosquitto/config && chmod 644 /mosquitto/config/mosquitto.conf && chmod 640 /mosquitto/config/passwordfile'
log "passwordfile pronto."

log "Subindo Mosquitto..."
docker run -d \
  --name fiware-mosquitto \
  --hostname mosquitto \
  --restart always \
  --network vigia-network \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.mqttws.rule=Host(\`${SERVICES_DOMAIN}\`) && PathPrefix(\`/vigia/fiware/mosquitto\`)" \
  --label "traefik.http.routers.mqttws.entrypoints=websecure" \
  --label "traefik.http.routers.mqttws.tls=true" \
  --label "traefik.http.routers.mqttws.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.mqttws.loadbalancer.server.port=9001" \
  --label "traefik.http.middlewares.strip-notifications.stripprefix.prefixes=/vigia/fiware/mosquitto" \
  --label "traefik.http.routers.mqttws.middlewares=strip-notifications,cors@file" \
  --label "traefik.tcp.routers.mosquitto-mqtts.rule=HostSNI(\`${MQTT_DOMAIN}\`)" \
  --label "traefik.tcp.routers.mosquitto-mqtts.entrypoints=mqtts" \
  --label "traefik.tcp.routers.mosquitto-mqtts.tls=true" \
  --label "traefik.tcp.routers.mosquitto-mqtts.tls.certresolver=letsencrypt" \
  --label "traefik.tcp.services.mosquitto-mqtts.loadbalancer.server.port=1883" \
  -v "$BASE_DIR/mosquitto":/mosquitto/config \
  eclipse-mosquitto:latest
log "Mosquitto OK."

# ─── AGUARDA ORION E MOSQUITTO ────────────────────────────────────────────────
warn "Aguardando Orion e Mosquitto iniciarem (10s)..."
sleep 10

# ─── FIWARE: STH-COMET ────────────────────────────────────────────────────────
log "Subindo STH-Comet..."
docker run -d \
  --name fiware-sth-comet \
  --hostname sth-comet \
  --restart always \
  --network vigia-network \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.sth.rule=Host(\`${SERVICES_DOMAIN}\`) && PathPrefix(\`/vigia/fiware/sth-comet\`)" \
  --label "traefik.http.routers.sth.entrypoints=websecure" \
  --label "traefik.http.routers.sth.tls=true" \
  --label "traefik.http.routers.sth.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.sth.loadbalancer.server.port=8666" \
  --label "traefik.http.routers.sth.middlewares=strip-sth,cors@file" \
  --label "traefik.http.middlewares.strip-sth.stripprefix.prefixes=/vigia/fiware/sth-comet" \
  -e STH_HOST=0.0.0.0 \
  -e STH_PORT=8666 \
  -e DB_PREFIX=sth_ \
  -e DB_URI=mongo-db-historical:27017 \
  -e DB_USERNAME=admin \
  -e DB_PASSWORD=admin123 \
  -e DB_AUTH_SOURCE=admin \
  -e LOGOPS_LEVEL=DEBUG \
  telefonicaiot/fiware-sth-comet
log "STH-Comet OK."

# ─── FIWARE: IOT AGENT ────────────────────────────────────────────────────────
log "Subindo IoT Agent..."
docker run -d \
  --name fiware-iot-agent \
  --hostname iot-agent \
  --restart always \
  --network vigia-network \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.iot.rule=Host(\`${SERVICES_DOMAIN}\`) && PathPrefix(\`/vigia/fiware/iot\`)" \
  --label "traefik.http.routers.iot.entrypoints=websecure" \
  --label "traefik.http.routers.iot.tls=true" \
  --label "traefik.http.routers.iot.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.iot.loadbalancer.server.port=4041" \
  --label "traefik.http.routers.iot.middlewares=strip-iot,cors@file" \
  --label "traefik.http.middlewares.strip-iot.stripprefix.prefixes=/vigia/fiware" \
  -e IOTA_CB_HOST=orion \
  -e IOTA_CB_PORT=1026 \
  -e IOTA_CB_NGSI_VERSION=v2 \
  -e IOTA_NORTH_PORT=4041 \
  -e IOTA_MONGO_HOST=mongo-db-internal \
  -e IOTA_MONGO_PORT=27017 \
  -e IOTA_MQTT_HOST=mosquitto \
  -e IOTA_MQTT_PORT=1883 \
  -e IOTA_MQTT_USERNAME=iotagent \
  -e IOTA_MQTT_PASSWORD=${MOSQUITTO_IOTAGENT_PASSWORD} \
  -e IOTA_LOG_LEVEL=DEBUG \
  -e IOTA_TIMESTAMP=true \
  -e IOTA_AUTOCAST=true \
  -e IOTA_PROVIDER_URL=http://iot-agent:4041 \
  fiware/iotagent-ul:latest
log "IoT Agent OK."

# ─── RESUMO ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Ambiente subido com sucesso!           ${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"