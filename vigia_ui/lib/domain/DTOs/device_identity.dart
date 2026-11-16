class DeviceIdentity {
  const DeviceIdentity({
    required this.deviceId,
    required this.name,
    required this.macAddress,
  });

  final String deviceId;
  final String name;
  final String macAddress;

  factory DeviceIdentity.fromJson(Map<String, dynamic> json) {
    final deviceId = json['device_id']?.toString();
    final name = json['name']?.toString() ?? 'Vigia';
    final macAddress = json['mac_address']?.toString();

    if (deviceId == null ||
        deviceId.isEmpty ||
        name.isEmpty ||
        macAddress == null ||
        macAddress.isEmpty) {
      throw const FormatException('Identity BLE inválida.');
    }

    return DeviceIdentity(
      deviceId: deviceId,
      name: name,
      macAddress: macAddress,
    );
  }
}
