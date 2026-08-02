import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/DTOs/device_provision_config.dart';
import 'package:vigia_ui/domain/DTOs/device_share_invite.dart';
import 'package:vigia_ui/domain/DTOs/new_device.dart';
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

  /// Returns null when the device is not registered (API 204 / empty body).
  Future<Device?> getDevice(String id) async {
    try {
      final response = await dio.get("$_devicesEndpoint/$id");

      if (response.statusCode == 204 || response.data == null) {
        return null;
      }

      final data = response.data;
      if (data is! Map<String, dynamic>) {
        return null;
      }

      return Device.fromJson(data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw UnauthorizedException(
          "Permissões insuficientes para acessar os dispositivos.",
        );
      }
      throw Exception('Failed to get device');
    } catch (e) {
      throw Exception('Failed to get device');
    }
  }

  Future<void> registerDevice(NewDevice device) async {
    try {
      await dio.post(
        "$_devicesEndpoint/register",
        data: {
          'id': device.id,
          'name': device.name,
          'macAddress': device.macAddress,
          'signPublicKey': device.signPublicKey,
        },
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw UnauthorizedException(
          "Permissões insuficientes para registrar o dispositivo.",
        );
      }
      final message = e.response?.data is Map
          ? (e.response?.data['errorMessage'] as String?)
          : null;
      throw Exception(message ?? 'Failed to register device');
    } catch (e) {
      rethrow;
    }
  }

  Future<DeviceProvisionConfig> getProvisionConfig() async {
    try {
      final response = await dio.get("$_devicesEndpoint/provision-config");
      final data = response.data;
      if (data is! Map<String, dynamic>) {
        throw Exception('Invalid provision config response');
      }
      final config = DeviceProvisionConfig.fromJson(data);
      if (config.fiwareApiKey.isEmpty) {
        throw Exception('Fiware API key missing from provision config');
      }
      return config;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw UnauthorizedException(
          "Permissões insuficientes para obter a configuração de provisionamento.",
        );
      }
      throw Exception(
        _apiErrorMessage(e) ?? 'Failed to get provision config',
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> trackDevice(String id) async {
    try {
      await dio.patch("$_devicesEndpoint/$id/users/track");
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw UnauthorizedException(
          "Permissões insuficientes para vincular o dispositivo.",
        );
      }
      throw Exception(_apiErrorMessage(e) ?? 'Failed to track device');
    } catch (e) {
      rethrow;
    }
  }

  String? _apiErrorMessage(DioException e) {
    final data = e.response?.data;
    if (data is! Map) return null;
    final message = data['errorMessage'] ?? data['ErrorMessage'];
    return message is String && message.isNotEmpty ? message : null;
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
