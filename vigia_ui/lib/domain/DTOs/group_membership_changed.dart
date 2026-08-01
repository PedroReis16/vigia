class GroupMembershipChanged {
  final String groupId;
  final String affectedUserId;
  final String changeType;
  final List<String> deviceIds;

  GroupMembershipChanged({
    required this.groupId,
    required this.affectedUserId,
    required this.changeType,
    required this.deviceIds,
  });

  factory GroupMembershipChanged.fromJson(Map<String, dynamic> json) {
    final rawDevices = json['deviceIds'] ?? json['DeviceIds'] ?? const [];
    final devices = rawDevices is List
        ? rawDevices.map((e) => e.toString()).toList()
        : <String>[];

    return GroupMembershipChanged(
      groupId: (json['groupId'] ?? json['GroupId']).toString(),
      affectedUserId: (json['affectedUserId'] ?? json['AffectedUserId'])
          .toString(),
      changeType: (json['changeType'] ?? json['ChangeType']).toString(),
      deviceIds: devices,
    );
  }

  static GroupMembershipChanged? tryParse(Object? raw) {
    if (raw == null) return null;
    if (raw is Map) {
      try {
        return GroupMembershipChanged.fromJson(Map<String, dynamic>.from(raw));
      } catch (_) {
        return null;
      }
    }
    return null;
  }

  bool get wasRemoved => changeType == 'removed';
  bool get wasJoined => changeType == 'joined';
}
