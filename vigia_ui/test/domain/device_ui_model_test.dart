import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';

void main() {
  group('DeviceUIModel', () {
    test('fromDTO sets isOwner from ownerId match', () {
      final device = Device(
        id: 'dev-1',
        name: 'Cam',
        ownerId: 'user-owner',
        room: DeviceRooms.kitchen,
      );

      final ownerModel = DeviceUIModel.fromDTO(device, 'user-owner');
      final guestModel = DeviceUIModel.fromDTO(device, 'user-guest');

      expect(ownerModel.isOwner, isTrue);
      expect(guestModel.isOwner, isFalse);
      expect(ownerModel.room, DeviceRooms.kitchen);
    });

    test('copyWith clearRoom clears room while preserving other fields', () {
      final model = DeviceUIModel(
        id: 'dev-1',
        name: 'Cam',
        nickname: 'Sala',
        room: DeviceRooms.livingRoom,
        isOwner: true,
        isClipsEnabled: true,
      );

      final cleared = model.copyWith(clearRoom: true);

      expect(cleared.room, isNull);
      expect(cleared.nickname, 'Sala');
      expect(cleared.isOwner, isTrue);
      expect(cleared.isClipsEnabled, isTrue);

      final updated = model.copyWith(
        nickname: 'Quarto',
        room: DeviceRooms.bedroom,
        isClipsEnabled: false,
      );

      expect(updated.nickname, 'Quarto');
      expect(updated.room, DeviceRooms.bedroom);
      expect(updated.isClipsEnabled, isFalse);
    });
  });
}
