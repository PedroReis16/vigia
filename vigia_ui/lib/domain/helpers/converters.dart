import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class Converters {
  static String translateDeviceRoom(BuildContext context, DeviceRooms room) {
    return switch (room) {
      DeviceRooms.kitchen => context.translations.kitchen,
      DeviceRooms.livingRoom => context.translations.livingRoom,
      DeviceRooms.bedroom => context.translations.bedroom,
      DeviceRooms.bathroom => context.translations.bathroom,
      DeviceRooms.garage => context.translations.garage,
      DeviceRooms.office => context.translations.office,
      DeviceRooms.backyard => context.translations.backyard,
      DeviceRooms.frontyard => context.translations.frontyard,
      DeviceRooms.notDefined => context.translations.roomNotDefined,
    };
  }
}
