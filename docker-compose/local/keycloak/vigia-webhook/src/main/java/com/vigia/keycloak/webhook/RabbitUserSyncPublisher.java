package com.vigia.keycloak.webhook;

import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import java.nio.charset.StandardCharsets;
import org.jboss.logging.Logger;

final class RabbitUserSyncPublisher {

    private static final Logger LOG = Logger.getLogger(RabbitUserSyncPublisher.class);

    private final String host;
    private final int port;
    private final String username;
    private final String password;
    private final String exchange;
    private final String routingKey;
    private final Object connectionLock = new Object();

    private Connection connection;

    RabbitUserSyncPublisher() {
        this("rabbitmq", 5672, "vigia", "vigia123", "vigia.users.direct_exchange", "users.sync");
    }

    RabbitUserSyncPublisher(
            String host,
            int port,
            String username,
            String password,
            String exchange,
            String routingKey) {
        this.host = host;
        this.port = port;
        this.username = username;
        this.password = password;
        this.exchange = exchange;
        this.routingKey = routingKey;
    }

    void publish(String payload) {
        try {
            Connection current = ensureConnection();
            AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                    .contentType("application/json")
                    .deliveryMode(2)
                    .build();
            try (Channel channel = current.createChannel()) {
                channel.basicPublish(exchange, routingKey, properties, payload.getBytes(StandardCharsets.UTF_8));
            }
        } catch (Exception ex) {
            LOG.warn("Falha ao publicar a sincronização de usuário no RabbitMQ", ex);
        }
    }

    void close() {
        synchronized (connectionLock) {
            if (connection == null) {
                return;
            }

            try {
                connection.close();
            } catch (Exception ex) {
                LOG.debug("Falha ao fechar a conexão com o RabbitMQ", ex);
            } finally {
                connection = null;
            }
        }
    }

    private Connection ensureConnection() throws Exception {
        synchronized (connectionLock) {
            if (connection != null && connection.isOpen()) {
                return connection;
            }

            ConnectionFactory factory = new ConnectionFactory();
            factory.setHost(host);
            factory.setPort(port);
            factory.setUsername(username);
            factory.setPassword(password);
            factory.setAutomaticRecoveryEnabled(true);
            connection = factory.newConnection("vigia-webhook");
            return connection;
        }
    }
}
