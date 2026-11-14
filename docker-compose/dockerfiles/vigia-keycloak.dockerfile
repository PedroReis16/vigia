# Keycloak de produção — context = docker-compose/
# Leva o listener vigia-webhook, o tema de login, o realm de import e o script
# que reaplica a configuração do realm (deploy/keycloak/setup-realm.sh).
FROM maven:3.9.9-eclipse-temurin-21 AS webhook
WORKDIR /src
COPY local/keycloak/vigia-webhook/pom.xml vigia-webhook/pom.xml
COPY local/keycloak/vigia-webhook/src vigia-webhook/src
RUN mvn -f vigia-webhook/pom.xml -B -DskipTests package

FROM quay.io/keycloak/keycloak:26.0 AS builder
ENV KC_DB=postgres \
    KC_HTTP_RELATIVE_PATH=/auth \
    KC_HEALTH_ENABLED=true
COPY --from=webhook --chown=keycloak:keycloak /src/vigia-webhook/target/vigia-webhook.jar /opt/keycloak/providers/vigia-webhook.jar
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.0
COPY --from=builder --chown=keycloak:keycloak /opt/keycloak/ /opt/keycloak/
COPY --chown=keycloak:keycloak local/keycloak/themes/vigia /opt/keycloak/themes/vigia
COPY --chown=keycloak:keycloak local/keycloak/realm-export.json /opt/keycloak/data/import/vigia-realm.json
COPY --chown=keycloak:keycloak local/keycloak/user-profile.json /opt/keycloak/setup/user-profile.json
COPY --chown=keycloak:keycloak deploy/keycloak/setup-realm.sh /opt/keycloak/setup/setup-realm.sh
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--optimized", "--import-realm"]
