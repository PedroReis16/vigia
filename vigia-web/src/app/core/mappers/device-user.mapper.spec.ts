import { DeviceUserMapper } from './device-user.mapper';

describe('DeviceUserMapper', () => {
  it('maps dto to entity', () => {
    const user = DeviceUserMapper.fromDto({
      id: 'u1',
      name: 'Alice',
      userPictureUrl: 'https://example.com/p.png',
      isOwner: true,
    });

    expect(user.id).toBe('u1');
    expect(user.name).toBe('Alice');
    expect(user.userPictureUrl).toBe('https://example.com/p.png');
    expect(user.isOwner).toBe(true);
  });

  it('maps dto list', () => {
    const users = DeviceUserMapper.fromDtoList([
      { id: 'u1', name: 'Alice', isOwner: true },
      { id: 'u2', name: 'Bob', isOwner: false },
    ]);

    expect(users).toHaveLength(2);
    expect(users[1].name).toBe('Bob');
  });
});
