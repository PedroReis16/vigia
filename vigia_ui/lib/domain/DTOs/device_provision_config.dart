class DeviceProvisionConfig {
  final String fiwareApiKey;
  final String streamIngestUrl;

  const DeviceProvisionConfig({
    required this.fiwareApiKey,
    required this.streamIngestUrl,
  });

  factory DeviceProvisionConfig.fromJson(Map<String, dynamic> json) {
    return DeviceProvisionConfig(
      fiwareApiKey: json['fiwareApiKey'] as String? ?? '',
      streamIngestUrl: json['streamIngestUrl'] as String? ?? '',
    );
  }
}
