import 'package:vigia_ui/domain/enums/device_rooms.dart';

class Device {
  final String id;
  final String name;
  final String? nickname;
  final String ownerId;
  final String? thumbnailUrl;
  final DeviceRooms? room;
  final bool isRunning;
  final bool isClipsEnabled;

  Device({
    required this.id,
    required this.name,
    this.nickname,
    required this.ownerId,
    this.room,
    this.thumbnailUrl,
    this.isRunning = false,
    this.isClipsEnabled = false,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id'].toString(),
      name: json['name'] as String? ?? '',
      nickname: json['nickname'] as String?,
      ownerId: json['ownerId']?.toString() ?? '',
      thumbnailUrl: json['thumbnailUrl'] as String?,
      room: DeviceRoomsExtension.fromString(json['room'] as String?),
      isRunning: json['isRunning'] as bool? ?? false,
      isClipsEnabled: json['isClipsEnabled'] as bool? ?? false,
    );
  }
}
