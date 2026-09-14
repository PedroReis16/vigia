import { environment } from '@environments/environment';
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

  it('resolves relative picture paths against apiUrl', () => {
    const user = DeviceUserMapper.fromDto({
      id: 'u1',
      name: 'Alice',
      userPictureUrl: 'pictures/user.jpg',
      isOwner: false,
    });

    const apiBase = environment.apiUrl.replace(/\/$/, '');
    expect(user.userPictureUrl).toBe(`${apiBase}/pictures/user.jpg`);
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
