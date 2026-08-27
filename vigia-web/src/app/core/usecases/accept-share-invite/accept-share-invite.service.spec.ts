import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { vi } from 'vitest';
import { of, throwError } from 'rxjs';
import { DevicesService } from '@core/services';
import { DevicesUseCaseError } from '../devices-use-case.error';
import { AcceptShareInviteService } from './accept-share-invite.service';

describe('AcceptShareInviteService', () => {
  let service: AcceptShareInviteService;
  let devicesService: { acceptShareInvite: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    devicesService = { acceptShareInvite: vi.fn() };
    TestBed.configureTestingModule({
      providers: [
        AcceptShareInviteService,
        { provide: DevicesService, useValue: devicesService },
      ],
    });
    service = TestBed.inject(AcceptShareInviteService);
  });

  it('accepts share invite', async () => {
    devicesService.acceptShareInvite.mockReturnValue(of(undefined));

    await service.execute('invite-token');

    expect(devicesService.acceptShareInvite).toHaveBeenCalledWith('invite-token');
  });

  it('maps http errors', async () => {
    devicesService.acceptShareInvite.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 400 })),
    );

    await expect(service.execute('bad-token')).rejects.toBeInstanceOf(DevicesUseCaseError);
  });
});
