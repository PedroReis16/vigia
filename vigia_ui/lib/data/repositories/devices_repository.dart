import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/DTOs/device_share_invite.dart';
import 'package:vigia_ui/domain/DTOs/user.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';
import 'package:vigia_ui/domain/exceptions/unauthroized_exception.dart';

class DevicesRepository {
  DevicesRepository(this.dio);

  final Dio dio;

  static const String _devicesEndpoint = '/devices';

  Future<List<Device>> getDevices() async {
    try {
      final response = await dio.get("$_devicesEndpoint/list");

      // API may return 204 No Content when the user has no devices.
      if (response.statusCode == 204 || response.data == null) {
        return [];
      }

      final data = response.data;
      if (data is! List) {
        return [];
      }

      return data.map((device) => Device.fromJson(device)).toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw UnauthorizedException(
          "Permissões insuficientes para acessar os dispositivos.",
        );
      }
      throw Exception('Failed to get devices');
    } catch (e) {
      throw Exception('Failed to get devices');
    }
  }

  Future<List<DeviceUser>> getDeviceUsers(String deviceId) async {
    try {
      final response = await dio.get("$_devicesEndpoint/$deviceId/users");

      List<DeviceUser> users = (response.data as List)
          .map((user) => DeviceUser.fromJson(user))
          .toList();

      return users;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw UnauthorizedException(
          "Permissões insuficientes para acessar os dispositivos.",
        );
      }
      throw Exception('Failed to get device users');
    } catch (e) {
      throw Exception('Failed to get device users');
    }
  }

  Future<DeviceShareInvite> generateShareLink(String deviceId) async {
    try {
      final response = await dio.get(
        "$_devicesEndpoint/$deviceId/share/generate",
      );
      return DeviceShareInvite.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw UnauthorizedException(
          "Permissões insuficientes para compartilhar o dispositivo.",
        );
      }
      final message = e.response?.data is Map
          ? (e.response?.data['errorMessage'] as String?)
          : null;
      throw Exception(message ?? 'Failed to generate share link');
    } catch (e) {
      rethrow;
    }
  }

  Future<void> acceptShareInvite(String token) async {
    try {
      await dio.post(
        "$_devicesEndpoint/share/accept",
        data: {'token': token},
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw UnauthorizedException(
          "Permissões insuficientes para aceitar o convite.",
        );
      }
      final message = e.response?.data is Map
          ? (e.response?.data['errorMessage'] as String?)
          : null;
      throw Exception(message ?? 'Failed to accept share invite');
    } catch (e) {
      rethrow;
    }
  }

  Future<void> removeDeviceUser(String deviceId, String userId) async {
    try {
      await dio.delete("$_devicesEndpoint/$deviceId/users/$userId");
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw UnauthorizedException(
          "Permissões insuficientes para remover o usuário.",
        );
      }
      final message = e.response?.data is Map
          ? (e.response?.data['errorMessage'] as String?)
          : null;
      throw Exception(message ?? 'Failed to remove device user');
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateDevice(
    String deviceId, {
    String? nickname,
    DeviceRooms? room,
    bool? isClipsEnabled,
  }) async {
    try {
      await dio.put(
        "$_devicesEndpoint/$deviceId",
        data: {
          "nickname": nickname,
          "room": room?.toApiString(),
          "isClipsEnabled": isClipsEnabled,
        },
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw UnauthorizedException(
          "Permissões insuficientes para acessar os dispositivos.",
        );
      }
      throw Exception('Failed to update device');
    } catch (e) {
      throw Exception('Failed to update device');
    }
  }
}
