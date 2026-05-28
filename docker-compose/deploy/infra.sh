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
 
# ─── REDE ─────────────────────────────────────────────────────────────────────
log "Criando rede vigia-network..."
docker network inspect vigia-network &>/dev/null || docker network create vigia-network
log "Rede vigia-network pronta."
 
# ─── REDIS ────────────────────────────────────────────────────────────────────
log "Subindo Redis..."
docker run -d \
  --name vigia-redis \
  --restart unless-stopped \
  --network vigia-network \
  -p 6379:6379 \
  redis:latest
log "Redis OK."
 
# ─── POSTGRES ─────────────────────────────────────────────────────────────────
log "Subindo Postgres..."
docker run -d \
  --name vigia-postgres \
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
  -v "$BASE_DIR/minio_data":/data \
  quay.io/minio/minio:latest \
  server --console-address ":9001" /data
log "Minio OK."
 
# ─── MEDIAMTX ─────────────────────────────────────────────────────────────────
log "Subindo MediaMTX..."
docker run -d \
  --name vigia-mediamtx \
  --restart unless-stopped \
  --network vigia-network \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.mediamtx-play.rule=(Host(\`www.vigia-deteccoes.duckdns.org\`) || Host(\`vigia-deteccoes.duckdns.org\`)) && PathPrefix(\`/live\`)" \
  --label "traefik.http.routers.mediamtx-play.entrypoints=websecure" \
  --label "traefik.http.routers.mediamtx-play.tls=true" \
  --label "traefik.http.routers.mediamtx-play.tls.certresolver=letsencrypt" \
  --label "traefik.http.routers.mediamtx-play.priority=100" \
  --label "traefik.http.services.mediamtx-play.loadbalancer.server.port=8889" \
  --label "traefik.tcp.routers.mediamtx-ingest.rule=HostSNI(\`ingest-vigia-deteccoes.duckdns.org\`)" \
  --label "traefik.tcp.routers.mediamtx-ingest.entrypoints=websecure" \
  --label "traefik.tcp.routers.mediamtx-ingest.tls=true" \
  --label "traefik.tcp.routers.mediamtx-ingest.tls.certresolver=letsencrypt" \
  --label "traefik.tcp.services.mediamtx-ingest.loadbalancer.server.port=1935" \
  -v "$BASE_DIR/mediamtx/mediamtx.yml":/mediamtx.yml:ro \
  bluenviron/mediamtx:latest
log "MediaMTX OK."
 
# ─── TRAEFIK ──────────────────────────────────────────────────────────────────
log "Subindo Traefik..."
docker run -d \
  --name traefik \
  --restart always \
  --network vigia-network \
  -p 80:80 \
  -p 443:443 \
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
  --label "traefik.http.routers.portainer.rule=Host(\`portainer-vigia.duckdns.org\`)" \
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
  --label "traefik.http.routers.orion.rule=(Host(\`vigia-deteccoes.duckdns.org\`) || Host(\`www.vigia-deteccoes.duckdns.org\`)) && PathPrefix(\`/fiware/orion\`)" \
  --label "traefik.http.routers.orion.entrypoints=websecure" \
  --label "traefik.http.routers.orion.tls=true" \
  --label "traefik.http.routers.orion.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.orion.loadbalancer.server.port=1026" \
  --label "traefik.http.routers.orion.middlewares=strip-orion,cors@file" \
  --label "traefik.http.middlewares.strip-orion.stripprefix.prefixes=/fiware/orion" \
  fiware/orion:3.11.0 \
  -dbhost mongo-db-historical \
  -dbuser admin \
  -dbpwd admin123 \
  -dbAuthDb admin \
  -corsOrigin __ALL \
  -corsMaxAge 600
log "Orion OK."
 
# ─── FIWARE: MOSQUITTO ────────────────────────────────────────────────────────
log "Subindo Mosquitto..."
docker run -d \
  --name fiware-mosquitto \
  --hostname mosquitto \
  --restart always \
  --network vigia-network \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.mqttws.rule=(Host(\`vigia-deteccoes.duckdns.org\`) || Host(\`www.vigia-deteccoes.duckdns.org\`)) && PathPrefix(\`/fiware/mosquitto\`)" \
  --label "traefik.http.routers.mqttws.entrypoints=websecure" \
  --label "traefik.http.routers.mqttws.tls=true" \
  --label "traefik.http.routers.mqttws.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.mqttws.loadbalancer.server.port=9001" \
  --label "traefik.http.middlewares.strip-notifications.stripprefix.prefixes=/fiware/mosquitto" \
  --label "traefik.http.routers.mqttws.middlewares=strip-notifications,cors@file" \
  -v "$BASE_DIR/mosquitto/mosquitto.conf":/mosquitto/config/mosquitto.conf \
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
  --label "traefik.http.routers.sth.rule=(Host(\`vigia-deteccoes.duckdns.org\`) || Host(\`www.vigia-deteccoes.duckdns.org\`)) && PathPrefix(\`/fiware/sth-comet\`)" \
  --label "traefik.http.routers.sth.entrypoints=websecure" \
  --label "traefik.http.routers.sth.tls=true" \
  --label "traefik.http.routers.sth.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.sth.loadbalancer.server.port=8666" \
  --label "traefik.http.routers.sth.middlewares=strip-sth,cors@file" \
  --label "traefik.http.middlewares.strip-sth.stripprefix.prefixes=/fiware/sth-comet" \
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
  --label "traefik.http.routers.iot.rule=(Host(\`vigia-deteccoes.duckdns.org\`) || Host(\`www.vigia-deteccoes.duckdns.org\`)) && PathPrefix(\`/fiware/iot-agent\`)" \
  --label "traefik.http.routers.iot.entrypoints=websecure" \
  --label "traefik.http.routers.iot.tls=true" \
  --label "traefik.http.routers.iot.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.iot.loadbalancer.server.port=4041" \
  --label "traefik.http.routers.iot.middlewares=strip-iot,cors@file" \
  --label "traefik.http.middlewares.strip-iot.stripprefix.prefixes=/fiware/iot-agent" \
  -e IOTA_CB_HOST=orion \
  -e IOTA_CB_PORT=1026 \
  -e IOTA_CB_NGSI_VERSION=v2 \
  -e IOTA_NORTH_PORT=4041 \
  -e IOTA_MONGO_HOST=mongo-db-internal \
  -e IOTA_MONGO_PORT=27017 \
  -e IOTA_MQTT_HOST=mosquitto \
  -e IOTA_MQTT_PORT=1883 \
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