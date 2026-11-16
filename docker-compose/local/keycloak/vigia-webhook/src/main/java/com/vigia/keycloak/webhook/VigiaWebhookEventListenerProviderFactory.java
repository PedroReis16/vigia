package com.vigia.keycloak.webhook;

import org.keycloak.Config;
import org.keycloak.events.EventListenerProvider;
import org.keycloak.events.EventListenerProviderFactory;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;

public final class VigiaWebhookEventListenerProviderFactory implements EventListenerProviderFactory {

    static final String PROVIDER_ID = "vigia-webhook";

    private RabbitUserSyncPublisher publisher = new RabbitUserSyncPublisher();

    @Override
    public EventListenerProvider create(KeycloakSession session) {
        return new VigiaWebhookEventListenerProvider(session, publisher);
    }

    @Override
    public void init(Config.Scope config) {
        publisher = new RabbitUserSyncPublisher(
                config.get("host", "rabbitmq"),
                config.getInt("port", 5672),
                config.get("username", "vigia"),
                config.get("password", "vigia123"),
                config.get("exchange", "vigia.users.direct_exchange"),
                config.get("routing-key", "users.sync"));
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
    }

    @Override
    public void close() {
        publisher.close();
    }

    @Override
    public String getId() {
        return PROVIDER_ID;
    }
}
