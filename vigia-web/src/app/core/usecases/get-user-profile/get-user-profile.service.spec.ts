import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { UserProfileHttpService, UserProfileStoreService } from '@core/services';
import { ProfileUseCaseError } from '../profile-use-case.error';
import { GetUserProfileService } from './get-user-profile.service';

describe('GetUserProfileService', () => {
  let service: GetUserProfileService;
  let http: { getProfile: ReturnType<typeof vi.fn> };
  let store: UserProfileStoreService;

  beforeEach(() => {
    http = { getProfile: vi.fn() };
    TestBed.configureTestingModule({
      providers: [{ provide: UserProfileHttpService, useValue: http }],
    });
    service = TestBed.inject(GetUserProfileService);
    store = TestBed.inject(UserProfileStoreService);
    store.set(null);
  });

  it('stores the mapped profile', async () => {
    http.getProfile.mockReturnValue(
      of({
        id: 'user-1',
        name: 'Ana Lima',
        firstName: 'Ana',
        lastName: 'Lima',
        email: 'ana@vigia.test',
        phone: '11999990000',
        pictureUrl: null,
      }),
    );

    const profile = await service.execute();

    expect(profile.name).toBe('Ana Lima');
    expect(profile.email).toBe('ana@vigia.test');
    expect(store.profile()).toEqual(profile);
  });

  it('maps HTTP failures to a profile error', async () => {
    http.getProfile.mockReturnValue(throwError(() => new HttpErrorResponse({ status: 500 })));

    await expect(service.execute()).rejects.toBeInstanceOf(ProfileUseCaseError);
  });
});
