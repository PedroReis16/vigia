FROM keycloak/keycloak:26.6.1

# (opcional) defaults – podem ser sobrescritos no compose
ENV KEYCLOAK_ADMIN=admin \
    KEYCLOAK_ADMIN_PASSWORD=admin \
    KC_DB=postgres \
    KC_DB_URL=jdbc:postgresql://postgres:5432/keycloakdb \
    KC_DB_USERNAME=keycloak \
    KC_DB_PASSWORD=keycloak \
    KC_DB_SCHEMA=keycloak \
    KC_HOSTNAME=localhost \
    KC_HTTP_PORT=8080 \
    RABBITMQ_HOST=rabbitmq \
    RABBITMQ_USER=admin \
    RABBITMQ_PASSWORD=admin 

# Build necessário após adicionar providers/temas
RUN /opt/keycloak/bin/kc.sh build

EXPOSE 8080

# Start padrão; você pode adicionar flags extras aqui se quiser
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]