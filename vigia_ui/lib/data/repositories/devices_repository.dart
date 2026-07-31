import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/exceptions/unauthroized_exception.dart';

class DevicesRepository {
  DevicesRepository(this.dio);

  final Dio dio;

  static const String _devicesEndpoint = '/devices';

  Future<List<Device>> getDevices() async {
    try {
      final response = await dio.get("$_devicesEndpoint/list");

      List<Device> devices = (response.data as List)
          .map((device) => Device.fromJson(device))
          .toList();

      return devices;
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
}
