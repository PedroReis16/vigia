import 'package:vigia_ui/domain/enums/device_rooms.dart';

class Device {
  final String id;
  final String nickname;
  final String ownerId;
  final String? thumbnailUrl;
  final DeviceRooms? room;

  Device({
    required this.id,
    required this.nickname,
    required this.ownerId,
    this.room,
    this.thumbnailUrl,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id'],
      nickname: json['nickname'] ?? json['name'],
      ownerId: json['ownerId'],
      thumbnailUrl: json['thumbnailUrl'],
      room: DeviceRoomsExtension.fromString(json['room']),
    );
  }
}
