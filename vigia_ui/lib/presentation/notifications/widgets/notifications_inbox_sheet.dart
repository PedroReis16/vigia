import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/models/user_notification.dart';
import 'package:vigia_ui/presentation/notifications/providers/notifications_provider.dart';

Future<void> showNotificationsInboxSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    useRootNavigator: true,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) {
      final height = MediaQuery.sizeOf(context).height * 0.72;
      return SizedBox(
        height: height,
        child: const NotificationsInboxSheet(),
      );
    },
  );
}

class NotificationsInboxSheet extends ConsumerWidget {
  const NotificationsInboxSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final inbox = ref.watch(notificationsInboxProvider);
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 8, 8),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'Notificações',
                  style: theme.textTheme.titleLarge,
                ),
              ),
              TextButton(
                onPressed: () =>
                    ref.read(notificationsInboxProvider.notifier).markAllRead(),
                child: const Text('Marcar todas'),
              ),
            ],
          ),
        ),
        Expanded(
          child: inbox.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, _) => Center(
              child: TextButton(
                onPressed: () =>
                    ref.read(notificationsInboxProvider.notifier).refresh(),
                child: const Text('Tentar novamente'),
              ),
            ),
            data: (data) {
              if (data.items.isEmpty) {
                return const Center(child: Text('Nenhuma notificação'));
              }

              return RefreshIndicator(
                onRefresh: () =>
                    ref.read(notificationsInboxProvider.notifier).refresh(),
                child: ListView.separated(
                  padding: const EdgeInsets.only(bottom: 24),
                  itemCount: data.items.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final item = data.items[index];
                    return _NotificationTile(notification: item);
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _NotificationTile extends ConsumerWidget {
  const _NotificationTile({required this.notification});

  final UserNotification notification;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return ListTile(
      leading: Icon(
        notification.read
            ? Icons.notifications_none_outlined
            : Icons.notifications_active,
        color: notification.read
            ? theme.colorScheme.onSurfaceVariant
            : theme.colorScheme.primary,
      ),
      title: Text(
        notification.title,
        style: TextStyle(
          fontWeight: notification.read ? FontWeight.w400 : FontWeight.w600,
        ),
      ),
      subtitle: Text(notification.body),
      onTap: () async {
        await ref
            .read(notificationsInboxProvider.notifier)
            .markRead(notification.id);
        if (!context.mounted) return;
        Navigator.of(context).pop();
        context.go('${AppRoutes.devicesPage}/${notification.deviceId}');
      },
    );
  }
}
