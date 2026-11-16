import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/models/user_notification.dart';

class NotificationsRepository {
  NotificationsRepository(this._dio);

  final Dio _dio;

  Future<NotificationInbox> list({int? skip, int? take}) async {
    final query = <String, dynamic>{};
    if (skip != null) query['skip'] = skip;
    if (take != null) query['take'] = take;

    final response = await _dio.get(
      '/notifications',
      queryParameters: query.isEmpty ? null : query,
    );

    final data = response.data;
    if (data is! Map) {
      return const NotificationInbox(items: [], unreadCount: 0);
    }

    return NotificationInbox.fromJson(Map<String, dynamic>.from(data));
  }

  Future<void> markRead(String notificationId) async {
    await _dio.post('/notifications/$notificationId/read');
  }

  Future<void> markAllRead() async {
    await _dio.post('/notifications/read-all');
  }

  Future<void> acknowledgeDeviceAlerts(String deviceId) async {
    await _dio.post('/devices/$deviceId/alerts/acknowledge');
  }
}
