class DeviceUser {
  final String id;
  final String name;
  final String? userPicture;
  final bool isOwner;

  DeviceUser({
    required this.id,
    required this.name,
    this.userPicture,
    required this.isOwner,
  });

  factory DeviceUser.fromJson(Map<String, dynamic> json) {
    return DeviceUser(
      id: json['id'],
      name: json['name'],
      userPicture: json['userPictureUrl'],
      isOwner: json['isOwner'],
    );
  }
}
