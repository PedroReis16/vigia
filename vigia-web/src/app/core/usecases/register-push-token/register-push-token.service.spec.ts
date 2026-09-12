import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { PushTokenHttpService } from '@core/services/http/push-token/push-token-http.service';
import { RegisterPushTokenService } from './register-push-token.service';

describe('RegisterPushTokenService', () => {
  let service: RegisterPushTokenService;
  let pushTokenHttp: { upsertToken: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    pushTokenHttp = { upsertToken: vi.fn(() => of(undefined)) };

    TestBed.configureTestingModule({
      providers: [
        RegisterPushTokenService,
        { provide: PushTokenHttpService, useValue: pushTokenHttp },
      ],
    });

    service = TestBed.inject(RegisterPushTokenService);
  });

  it('registers web push tokens', async () => {
    await service.execute('token-123');

    expect(pushTokenHttp.upsertToken).toHaveBeenCalledWith('token-123', 'web');
  });

  it('skips empty tokens', async () => {
    await service.execute('   ');

    expect(pushTokenHttp.upsertToken).not.toHaveBeenCalled();
  });
});
