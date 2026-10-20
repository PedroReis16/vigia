import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/dio_provider.dart';
import 'package:vigia_ui/data/repositories/notifications_repository.dart';

part 'notifications_repository_provider.g.dart';

@Riverpod(keepAlive: true)
NotificationsRepository notificationsRepository(Ref ref) =>
    NotificationsRepository(ref.read(dioProvider));
