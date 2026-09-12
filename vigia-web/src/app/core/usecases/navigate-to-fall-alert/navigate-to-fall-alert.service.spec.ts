import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { NavigateToFallAlertService } from './navigate-to-fall-alert.service';

describe('NavigateToFallAlertService', () => {
  let service: NavigateToFallAlertService;
  let router: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    router = { navigate: vi.fn().mockResolvedValue(true) };

    TestBed.configureTestingModule({
      providers: [NavigateToFallAlertService, { provide: Router, useValue: router }],
    });

    service = TestBed.inject(NavigateToFallAlertService);
  });

  it('navigates to device detail for fall alerts', async () => {
    const result = await service.execute({ type: 'fall', deviceId: 'device-1' });

    expect(result).toBe(true);
    expect(router.navigate).toHaveBeenCalledWith(['/devices', 'device-1']);
  });

  it('returns false for invalid payloads', async () => {
    const result = await service.execute({ type: 'other', deviceId: 'device-1' });

    expect(result).toBe(false);
    expect(router.navigate).not.toHaveBeenCalled();
  });
});
