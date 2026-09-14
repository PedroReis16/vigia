export interface GroupMembershipChangedDto {
  groupId: string;
  affectedUserId: string;
  changeType: string;
  deviceIds: string[];
}

export function parseGroupMembershipChanged(raw: unknown): GroupMembershipChangedDto | null {
  if (!raw || typeof raw !== 'object') {
    return null;
  }

  const json = raw as Record<string, unknown>;
  const rawDevices = json['deviceIds'] ?? json['DeviceIds'] ?? [];
  const deviceIds = Array.isArray(rawDevices)
    ? rawDevices.map((entry) => String(entry))
    : [];

  const groupId = json['groupId'] ?? json['GroupId'];
  const affectedUserId = json['affectedUserId'] ?? json['AffectedUserId'];
  const changeType = json['changeType'] ?? json['ChangeType'];

  if (groupId == null || affectedUserId == null || changeType == null) {
    return null;
  }

  return {
    groupId: String(groupId),
    affectedUserId: String(affectedUserId),
    changeType: String(changeType),
    deviceIds,
  };
}
