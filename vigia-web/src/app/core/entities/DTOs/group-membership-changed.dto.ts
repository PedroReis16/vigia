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

export function sameId(left: string | null | undefined, right: string | null | undefined): boolean {
  if (!left || !right) {
    return false;
  }

  return left.localeCompare(right, undefined, { sensitivity: 'accent' }) === 0;
}

export function eventIncludesDevice(event: GroupMembershipChangedDto, deviceId: string): boolean {
  return event.deviceIds.some((id) => sameId(id, deviceId));
}

export function currentUserLostDevice(
  event: GroupMembershipChangedDto,
  currentUserId: string | null | undefined,
  deviceId: string,
): boolean {
  return event.changeType === 'removed'
    && sameId(event.affectedUserId, currentUserId)
    && eventIncludesDevice(event, deviceId);
}

export function membershipEventKey(event: GroupMembershipChangedDto): string {
  return `${event.groupId}|${event.affectedUserId}|${event.changeType}|${event.deviceIds.join(',')}`;
}

export function isDuplicateMembershipEvent(
  previous: { key: string; at: number } | null,
  event: GroupMembershipChangedDto,
  now: number,
  windowMs = 1000,
): boolean {
  if (!previous) {
    return false;
  }

  return previous.key === membershipEventKey(event) && now - previous.at < windowMs;
}
