import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/data/services/push_notification_coordinator.dart';

part 'push_notification_provider.g.dart';

@Riverpod(keepAlive: true)
PushNotificationCoordinator pushNotificationCoordinator(Ref ref) {
  final coordinator = PushNotificationCoordinator(ref);
  ref.onDispose(coordinator.dispose);
  return coordinator;
}
