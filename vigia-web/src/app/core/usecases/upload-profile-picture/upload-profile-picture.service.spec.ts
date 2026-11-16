import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { throwError } from 'rxjs';
import { vi } from 'vitest';
import { UserProfileHttpService } from '@core/services';
import { ProfileUseCaseError } from '../profile-use-case.error';
import { UploadProfilePictureService } from './upload-profile-picture.service';

describe('UploadProfilePictureService', () => {
  let service: UploadProfilePictureService;
  let http: { uploadPicture: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    http = { uploadPicture: vi.fn() };
    TestBed.configureTestingModule({
      providers: [{ provide: UserProfileHttpService, useValue: http }],
    });
    service = TestBed.inject(UploadProfilePictureService);
  });

  it('maps an invalid picture to the validation message', async () => {
    http.uploadPicture.mockReturnValue(
      throwError(() => new HttpErrorResponse({
        status: 400,
        error: { errorCode: 'INVALID_PROFILE_PICTURE' },
      })),
    );

    await expect(service.execute(new File(['x'], 'a.gif'))).rejects.toEqual(
      expect.objectContaining({ messageKey: 'PROFILE.PICTURE_INVALID' }),
    );
    await expect(service.execute(new File(['x'], 'a.gif'))).rejects.toBeInstanceOf(ProfileUseCaseError);
  });
});
