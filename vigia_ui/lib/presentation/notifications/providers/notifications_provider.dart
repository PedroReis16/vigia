import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/notifications_repository_provider.dart';
import 'package:vigia_ui/domain/models/user_notification.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'notifications_provider.g.dart';

@Riverpod(keepAlive: true)
class NotificationsInbox extends _$NotificationsInbox {
  @override
  FutureOr<NotificationInbox> build() async {
    final authenticated = await ref.watch(authSessionProvider.future);
    if (!authenticated) {
      return const NotificationInbox(items: [], unreadCount: 0);
    }

    return ref.read(notificationsRepositoryProvider).list();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final authenticated = await ref.read(authSessionProvider.future);
      if (!authenticated) {
        return const NotificationInbox(items: [], unreadCount: 0);
      }
      return ref.read(notificationsRepositoryProvider).list();
    });
  }

  Future<void> markRead(String notificationId) async {
    final current = state.asData?.value;
    if (current != null) {
      final nextItems = current.items
          .map(
            (item) => item.id == notificationId
                ? UserNotification(
                    id: item.id,
                    episodeId: item.episodeId,
                    deviceId: item.deviceId,
                    type: item.type,
                    title: item.title,
                    body: item.body,
                    createdAt: item.createdAt,
                    read: true,
                    readAt: item.readAt ?? DateTime.now(),
                  )
                : item,
          )
          .toList();
      state = AsyncData(
        NotificationInbox(
          items: nextItems,
          unreadCount: nextItems.where((item) => !item.read).length,
        ),
      );
    }

    try {
      await ref.read(notificationsRepositoryProvider).markRead(notificationId);
    } catch (_) {
      await refresh();
    }
  }

  Future<void> markAllRead() async {
    final current = state.asData?.value;
    if (current != null) {
      state = AsyncData(
        NotificationInbox(
          items: current.items
              .map(
                (item) => UserNotification(
                  id: item.id,
                  episodeId: item.episodeId,
                  deviceId: item.deviceId,
                  type: item.type,
                  title: item.title,
                  body: item.body,
                  createdAt: item.createdAt,
                  read: true,
                  readAt: item.readAt ?? DateTime.now(),
                ),
              )
              .toList(),
          unreadCount: 0,
        ),
      );
    }

    try {
      await ref.read(notificationsRepositoryProvider).markAllRead();
    } catch (_) {
      await refresh();
    }
  }
}
