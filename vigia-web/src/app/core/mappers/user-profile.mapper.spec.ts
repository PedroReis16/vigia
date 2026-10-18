import { UserProfileDto } from '@core/entities/DTOs/user-profile.dto';
import { environment } from '@environments/environment';
import { UserProfileMapper } from './user-profile.mapper';

describe('UserProfileMapper', () => {
  const apiBase = environment.apiUrl.replace(/\/$/, '');

  it('resolves a relative picture url', () => {
    const profile = UserProfileMapper.fromDto({
      id: 'user-1',
      name: 'Ana Lima',
      firstName: 'Ana',
      lastName: 'Lima',
      email: 'ana@vigia.test',
      phone: '11999990000',
      pictureUrl: 'users/user-1/picture?accessToken=tok&v=1',
    });

    expect(profile.name).toBe('Ana Lima');
    expect(profile.pictureUrl).toBe(`${apiBase}/users/user-1/picture?accessToken=tok&v=1`);
  });

  it('keeps a missing picture empty', () => {
    const profile = UserProfileMapper.fromDto({
      id: 'user-1',
      name: 'ana@vigia.test',
      firstName: '',
      lastName: '',
      email: 'ana@vigia.test',
      phone: '',
      pictureUrl: null,
    } satisfies UserProfileDto);

    expect(profile.pictureUrl).toBeNull();
    expect(profile.canDeleteAccount).toBe(true);
  });

  it('hides account deletion when the api forbids it', () => {
    const profile = UserProfileMapper.fromDto({
      id: 'admin',
      name: 'Super Admin',
      firstName: 'Super',
      lastName: 'Admin',
      email: 'admin@vigia.local',
      phone: '11999999999',
      canDeleteAccount: false,
    });

    expect(profile.canDeleteAccount).toBe(false);
  });
});
