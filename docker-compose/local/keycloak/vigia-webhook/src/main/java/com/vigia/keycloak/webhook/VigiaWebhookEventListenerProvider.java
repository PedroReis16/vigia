package com.vigia.keycloak.webhook;

import java.util.regex.Pattern;
import org.jboss.logging.Logger;
import org.keycloak.events.Event;
import org.keycloak.events.EventListenerProvider;
import org.keycloak.events.EventType;
import org.keycloak.events.admin.AdminEvent;
import org.keycloak.events.admin.OperationType;
import org.keycloak.events.admin.ResourceType;
import org.keycloak.models.AbstractKeycloakTransaction;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;

final class VigiaWebhookEventListenerProvider implements EventListenerProvider {

    private static final Logger LOG = Logger.getLogger(VigiaWebhookEventListenerProvider.class);
    private static final Pattern USER_PATH = Pattern.compile(
            "^users/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$");

    private final KeycloakSession session;
    private final RabbitUserSyncPublisher publisher;

    VigiaWebhookEventListenerProvider(KeycloakSession session, RabbitUserSyncPublisher publisher) {
        this.session = session;
        this.publisher = publisher;
    }

    @Override
    public void onEvent(Event event) {
        if (event == null || event.getType() == null || event.getUserId() == null) {
            return;
        }

        String operation = operationFor(event.getType());
        if (operation == null) {
            return;
        }

        String payload = "delete".equals(operation)
                ? UserSyncPayload.delete(event.getUserId())
                : upsertFromSession(event.getRealmId(), event.getUserId());
        if (payload != null) {
            publishAfterCommit(payload);
        }
    }

    @Override
    public void onEvent(AdminEvent adminEvent, boolean includeRepresentation) {
        if (adminEvent == null || adminEvent.getResourceType() != ResourceType.USER) {
            return;
        }

        String userId = userIdFromPath(adminEvent.getResourcePath());
        if (userId == null || adminEvent.getOperationType() == null) {
            return;
        }

        OperationType operationType = adminEvent.getOperationType();
        if (operationType == OperationType.DELETE) {
            publishAfterCommit(UserSyncPayload.delete(userId));
            return;
        }

        if (operationType != OperationType.CREATE && operationType != OperationType.UPDATE) {
            return;
        }

        String payload = upsertFromSession(adminEvent.getRealmId(), userId);
        if (payload != null) {
            publishAfterCommit(payload);
        }
    }

    @Override
    public void close() {
    }

    private String upsertFromSession(String realmId, String userId) {
        RealmModel realm = session.realms().getRealm(realmId);
        if (realm == null) {
            return null;
        }

        UserModel user = session.users().getUserById(realm, userId);
        if (user == null) {
            return null;
        }

        return UserSyncPayload.upsert(
                user.getId(),
                user.getFirstName(),
                user.getLastName(),
                user.getEmail(),
                user.getFirstAttribute("phone"));
    }

    private void publishAfterCommit(String payload) {
        try {
            session.getTransactionManager().enlistAfterCompletion(new AbstractKeycloakTransaction() {
                @Override
                protected void commitImpl() {
                    publisher.publish(payload);
                }

                @Override
                protected void rollbackImpl() {
                }
            });
        } catch (RuntimeException ex) {
            LOG.warn("Não foi possível agendar a publicação do usuário no RabbitMQ", ex);
        }
    }

    private static String operationFor(EventType type) {
        return switch (type) {
            case REGISTER, LOGIN, UPDATE_PROFILE, UPDATE_EMAIL -> "upsert";
            case DELETE_ACCOUNT -> "delete";
            default -> null;
        };
    }

    private static String userIdFromPath(String resourcePath) {
        if (resourcePath == null || !USER_PATH.matcher(resourcePath).matches()) {
            return null;
        }

        return resourcePath.substring("users/".length());
    }
}
