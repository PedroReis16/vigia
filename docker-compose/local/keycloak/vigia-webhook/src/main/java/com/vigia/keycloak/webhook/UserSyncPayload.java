package com.vigia.keycloak.webhook;

final class UserSyncPayload {

    private UserSyncPayload() {
    }

    static String upsert(String id, String firstName, String lastName, String email, String phone) {
        return "{"
                + "\"operation\":\"upsert\","
                + "\"id\":" + jsonString(id) + ","
                + "\"firstName\":" + jsonString(firstName) + ","
                + "\"lastName\":" + jsonString(lastName) + ","
                + "\"email\":" + jsonString(email) + ","
                + "\"phone\":" + jsonString(phone)
                + "}";
    }

    static String delete(String id) {
        return "{"
                + "\"operation\":\"delete\","
                + "\"id\":" + jsonString(id)
                + "}";
    }

    private static String jsonString(String value) {
        if (value == null) {
            return "null";
        }

        StringBuilder builder = new StringBuilder(value.length() + 2);
        builder.append('"');
        for (int i = 0; i < value.length(); i++) {
            char current = value.charAt(i);
            switch (current) {
                case '\\' -> builder.append("\\\\");
                case '"' -> builder.append("\\\"");
                case '\n' -> builder.append("\\n");
                case '\r' -> builder.append("\\r");
                case '\t' -> builder.append("\\t");
                default -> {
                    if (current < 0x20) {
                        builder.append(String.format("\\u%04x", (int) current));
                    } else {
                        builder.append(current);
                    }
                }
            }
        }
        builder.append('"');
        return builder.toString();
    }
}
