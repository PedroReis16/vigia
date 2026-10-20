class DeviceClientCertificate {
  const DeviceClientCertificate({
    required this.certificate,
    required this.privateKey,
  });

  final String certificate;
  final String privateKey;

  static DeviceClientCertificate? fromJson(Object? data) {
    if (data is! Map) return null;
    final certificate = data['certificate'];
    final privateKey = data['privateKey'];
    if (certificate is! String || certificate.isEmpty) return null;
    if (privateKey is! String || privateKey.isEmpty) return null;
    return DeviceClientCertificate(
      certificate: certificate,
      privateKey: privateKey,
    );
  }
}
