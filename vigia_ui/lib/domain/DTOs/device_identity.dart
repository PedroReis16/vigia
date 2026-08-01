class DeviceIdentity {
  const DeviceIdentity({
    required this.deviceId,
    required this.signPub,
    required this.ecdhPub,
    required this.name,
    required this.macAddress,
  });

  final String deviceId;
  final String signPub;
  final String ecdhPub;
  final String name;
  final String macAddress;

  factory DeviceIdentity.fromJson(Map<String, dynamic> json) {
    final deviceId = json['device_id']?.toString();
    final signPub = json['sign_pub']?.toString();
    final ecdhPub = json['ecdh_pub']?.toString();
    final name = json['name']?.toString() ?? 'Vigia';
    final macAddress = json['mac_address']?.toString();

    if (deviceId == null ||
        deviceId.isEmpty ||
        signPub == null ||
        signPub.isEmpty ||
        ecdhPub == null ||
        ecdhPub.isEmpty ||
        name.isEmpty ||
        macAddress == null ||
        macAddress.isEmpty) {
      throw const FormatException('Identity BLE inválida.');
    }

    return DeviceIdentity(
      deviceId: deviceId,
      signPub: signPub,
      ecdhPub: ecdhPub,
      name: name,
      macAddress: macAddress,
    );
  }
}
