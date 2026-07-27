class DeviceIdentity {
  const DeviceIdentity({
    required this.deviceId,
    required this.signPub,
    required this.ecdhPub,
  });

  final String deviceId;
  final String signPub;
  final String ecdhPub;

  factory DeviceIdentity.fromJson(Map<String, dynamic> json) {
    final deviceId = json['device_id']?.toString();
    final signPub = json['sign_pub']?.toString();
    final ecdhPub = json['ecdh_pub']?.toString();

    if (deviceId == null ||
        deviceId.isEmpty ||
        signPub == null ||
        signPub.isEmpty ||
        ecdhPub == null ||
        ecdhPub.isEmpty) {
      throw const FormatException('Identity BLE inválida.');
    }

    return DeviceIdentity(
      deviceId: deviceId,
      signPub: signPub,
      ecdhPub: ecdhPub,
    );
  }
}
