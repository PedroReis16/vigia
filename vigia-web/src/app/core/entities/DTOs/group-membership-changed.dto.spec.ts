import { currentUserLostDevice, isDuplicateMembershipEvent } from './group-membership-changed.dto';

const event = {
  groupId: 'g',
  affectedUserId: 'u',
  changeType: 'joined',
  deviceIds: ['d'],
};

describe('isDuplicateMembershipEvent', () => {
  it('ignores the same payload inside the window', () => {
    const first = { key: 'g|u|joined|d', at: 1_000 };
    expect(isDuplicateMembershipEvent(first, event, 1_500)).toBe(true);
    expect(isDuplicateMembershipEvent(first, event, 2_000)).toBe(false);
    expect(isDuplicateMembershipEvent(null, event, 1_500)).toBe(false);
  });
});

describe('currentUserLostDevice', () => {
  it('matches the removed user and device ignoring id case', () => {
    expect(currentUserLostDevice(
      { groupId: 'g', affectedUserId: 'USER-1', changeType: 'removed', deviceIds: ['DEVICE-1'] },
      'user-1',
      'device-1',
    )).toBe(true);
  });

  it('ignores another member and a device list change', () => {
    const removedOther = {
      groupId: 'g',
      affectedUserId: 'user-2',
      changeType: 'removed',
      deviceIds: ['device-1'],
    };
    expect(currentUserLostDevice(removedOther, 'user-1', 'device-1')).toBe(false);
    expect(currentUserLostDevice(
      { ...removedOther, affectedUserId: 'user-1', changeType: 'devices_changed' },
      'user-1',
      'device-1',
    )).toBe(false);
  });
});
