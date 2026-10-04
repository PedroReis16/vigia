-- Isola o Keycloak no schema "keycloak" do database "vigia".
-- O entrypoint oficial só executa isto na primeira inicialização do data dir.
-- A senha precisa ser a mesma de KC_DB_PASSWORD no docker-compose.yaml.

CREATE ROLE keycloak WITH LOGIN PASSWORD 'senha_forte';

CREATE SCHEMA keycloak AUTHORIZATION keycloak;

REVOKE ALL ON SCHEMA keycloak FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA keycloak TO keycloak;

ALTER ROLE keycloak SET search_path TO keycloak;
REVOKE ALL ON SCHEMA public FROM keycloak;
