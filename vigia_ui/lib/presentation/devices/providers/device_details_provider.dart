import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';

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
