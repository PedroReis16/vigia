class DeviceProvisionConfig {
  final String fiwareApiKey;

  const DeviceProvisionConfig({
    required this.fiwareApiKey,
  });

  factory DeviceProvisionConfig.fromJson(Map<String, dynamic> json) {
    return DeviceProvisionConfig(
      fiwareApiKey: json['fiwareApiKey'] as String? ?? '',
    );
  }
}
