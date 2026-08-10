class DeviceShareInvite {
  final String token;
  final String inviteUrl;
  final DateTime expiresAt;

  DeviceShareInvite({
    required this.token,
    required this.inviteUrl,
    required this.expiresAt,
  });

  factory DeviceShareInvite.fromJson(Map<String, dynamic> json) {
    return DeviceShareInvite(
      token: json['token'] as String,
      inviteUrl: json['inviteUrl'] as String,
      expiresAt: DateTime.parse(json['expiresAt'] as String),
    );
  }
}
