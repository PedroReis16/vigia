import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/group_membership_changed.dart';

void main() {
  group('GroupMembershipChanged', () {
    test('parses camelCase JSON', () {
      final event = GroupMembershipChanged.fromJson({
        'groupId': 'g1',
        'affectedUserId': 'u1',
        'changeType': 'joined',
        'deviceIds': ['d1', 'd2'],
      });

      expect(event.groupId, 'g1');
      expect(event.affectedUserId, 'u1');
      expect(event.changeType, 'joined');
      expect(event.deviceIds, ['d1', 'd2']);
      expect(event.wasJoined, isTrue);
      expect(event.wasRemoved, isFalse);
    });

    test('parses PascalCase JSON', () {
      final event = GroupMembershipChanged.fromJson({
        'GroupId': 'g2',
        'AffectedUserId': 'u2',
        'ChangeType': 'removed',
        'DeviceIds': ['d3'],
      });

      expect(event.groupId, 'g2');
      expect(event.affectedUserId, 'u2');
      expect(event.changeType, 'removed');
      expect(event.deviceIds, ['d3']);
      expect(event.wasRemoved, isTrue);
      expect(event.wasJoined, isFalse);
    });

    test('tryParse returns event for valid map and null otherwise', () {
      expect(
        GroupMembershipChanged.tryParse({
          'groupId': 'g3',
          'affectedUserId': 'u3',
          'changeType': 'joined',
          'deviceIds': <String>[],
        }),
        isA<GroupMembershipChanged>(),
      );
      expect(GroupMembershipChanged.tryParse(null), isNull);
      expect(GroupMembershipChanged.tryParse('not-a-map'), isNull);
    });
  });
}
