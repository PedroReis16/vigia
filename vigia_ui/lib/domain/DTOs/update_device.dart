import 'package:vigia_ui/domain/enums/device_rooms.dart';

class UpdateDevice {
  final String? nickname;
  final DeviceRooms? room;
  final bool? isClipsEnabled;

  UpdateDevice({this.nickname, this.room, this.isClipsEnabled});
}
