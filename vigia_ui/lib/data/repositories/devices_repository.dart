import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';

class DevicesRepository {
  DevicesRepository(this.dio);

  final Dio dio;

  static const String _devicesEndpoint = '/devices';

  Future<List<Device>> getDevices() async {
    try {
      final response = await dio.get("$_devicesEndpoint/list");

      return response.data.map((device) => Device.fromJson(device)).toList();
    } catch (e) {
      throw Exception('Failed to get devices');
    }
  }
}
