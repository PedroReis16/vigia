import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/domain/DTOs/device_share_invite.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';

part 'device_details_provider.g.dart';

@riverpod
Future<List<UserUIModel>> getDeviceUsers(Ref ref, String deviceId) async {
  try {
    final users = await ref
        .read(devicesRepositoryProvider)
        .getDeviceUsers(deviceId);

    return users.map((user) => UserUIModel.fromDTO(user)).toList();
  } catch (e) {
    rethrow;
  }
}

@Riverpod(keepAlive: true)
class DeviceShareActions extends _$DeviceShareActions {
  @override
  AsyncValue<void> build() => const AsyncData(null);

  Future<DeviceShareInvite> generateShareLink(String deviceId) async {
    state = const AsyncLoading();
    try {
      final invite = await ref
          .read(devicesRepositoryProvider)
          .generateShareLink(deviceId);
      if (!ref.mounted) return invite;
      state = const AsyncData(null);
      return invite;
    } catch (e, st) {
      if (ref.mounted) state = AsyncError(e, st);
      rethrow;
    }
  }

  Future<void> acceptInvite(String token) async {
    state = const AsyncLoading();
    try {
      await ref.read(devicesRepositoryProvider).acceptShareInvite(token);
      if (!ref.mounted) return;
      await ref.read(devicesProvider.notifier).refresh(withDelay: false);
      if (!ref.mounted) return;
      state = const AsyncData(null);
    } catch (e, st) {
      if (ref.mounted) state = AsyncError(e, st);
      rethrow;
    }
  }

  Future<void> removeUser(String deviceId, String userId) async {
    state = const AsyncLoading();
    try {
      await ref
          .read(devicesRepositoryProvider)
          .removeDeviceUser(deviceId, userId);
      if (!ref.mounted) return;
      ref.invalidate(getDeviceUsersProvider(deviceId));
      await ref.read(devicesProvider.notifier).refresh(withDelay: false);
      if (!ref.mounted) return;
      state = const AsyncData(null);
    } catch (e, st) {
      if (ref.mounted) state = AsyncError(e, st);
      rethrow;
    }
  }
}
