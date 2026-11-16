FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY vigia-webhook/pom.xml vigia-webhook/pom.xml
COPY vigia-webhook/src vigia-webhook/src
RUN mvn -f vigia-webhook/pom.xml -B -DskipTests package

FROM quay.io/keycloak/keycloak:26.0
COPY --from=build --chown=keycloak:keycloak /src/vigia-webhook/target/vigia-webhook.jar /opt/keycloak/providers/vigia-webhook.jar
