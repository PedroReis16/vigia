import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';

class DeviceUIModel {
  final String id;
  final String name;
  final String? nickname;
  final String? thumbnailUrl;
  final DeviceRooms? room;
  final bool isClipsEnabled;
  final bool isRunning;
  final bool isOwner;

  DeviceUIModel({
    required this.id,
    required this.name,
    this.nickname,
    this.thumbnailUrl,
    this.room,
    this.isRunning = false,
    this.isOwner = false,
    this.isClipsEnabled = false,
  });

  factory DeviceUIModel.fromDTO(Device device, String userId) {
    return DeviceUIModel(
      id: device.id,
      name: device.name,
      nickname: device.nickname,
      thumbnailUrl: device.thumbnailUrl,
      room: device.room,
      isRunning: device.isRunning,
      isOwner: device.ownerId == userId,
      isClipsEnabled: device.isClipsEnabled,
    );
  }

  DeviceUIModel copyWith({
    String? nickname,
    DeviceRooms? room,
    bool? isClipsEnabled,
    bool clearRoom = false,
  }) {
    return DeviceUIModel(
      id: id,
      name: name,
      nickname: nickname ?? this.nickname,
      thumbnailUrl: thumbnailUrl,
      room: clearRoom ? null : (room ?? this.room),
      isRunning: isRunning,
      isOwner: isOwner,
      isClipsEnabled: isClipsEnabled ?? this.isClipsEnabled,
    );
  }
}
