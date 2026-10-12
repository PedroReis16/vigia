class UserNotification {
  const UserNotification({
    required this.id,
    required this.episodeId,
    required this.deviceId,
    required this.type,
    required this.title,
    required this.body,
    required this.createdAt,
    required this.read,
    this.readAt,
  });

  final String id;
  final String episodeId;
  final String deviceId;
  final String type;
  final String title;
  final String body;
  final DateTime createdAt;
  final bool read;
  final DateTime? readAt;

  factory UserNotification.fromJson(Map<String, dynamic> json) {
    return UserNotification(
      id: json['id']?.toString() ?? '',
      episodeId: json['episodeId']?.toString() ?? '',
      deviceId: json['deviceId']?.toString() ?? '',
      type: json['type']?.toString() ?? 'fall',
      title: json['title']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      createdAt: DateTime.tryParse(json['createdAt']?.toString() ?? '')?.toLocal() ??
          DateTime.now(),
      read: json['read'] == true,
      readAt: DateTime.tryParse(json['readAt']?.toString() ?? '')?.toLocal(),
    );
  }
}

class NotificationInbox {
  const NotificationInbox({
    required this.items,
    required this.unreadCount,
  });

  final List<UserNotification> items;
  final int unreadCount;

  factory NotificationInbox.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    final items = rawItems is List
        ? rawItems
            .whereType<Map>()
            .map((item) => UserNotification.fromJson(Map<String, dynamic>.from(item)))
            .toList()
        : <UserNotification>[];

    final unread = json['unreadCount'];
    return NotificationInbox(
      items: items,
      unreadCount: unread is int ? unread : int.tryParse(unread?.toString() ?? '') ?? 0,
    );
  }
}
