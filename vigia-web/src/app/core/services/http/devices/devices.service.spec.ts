import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { DevicesService } from './devices.service';

describe('DevicesService', () => {
  let service: DevicesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [DevicesService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(DevicesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('gets devices from relative /devices/list without Skip-Auth', () => {
    let response: unknown;

    service.getDevices().subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/devices/list');
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.has('Skip-Auth')).toBe(false);
    req.flush([
      {
        id: '1',
        name: 'Vigia-a1b2c3d4',
        nickname: 'Sala',
        room: 'LivingRoom',
        ownerId: 'u1',
        macAddress: 'AA:BB:CC:DD:EE:FF',
        thumbnailUrl: 'pictures/1.jpg',
        isRunning: true,
        isClipsEnabled: false,
      },
    ]);

    expect(response).toEqual([
      expect.objectContaining({ id: '1', nickname: 'Sala', isRunning: true }),
    ]);
  });

  it('returns empty array on 204', () => {
    let response: unknown;

    service.getDevices().subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/devices/list');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(response).toEqual([]);
  });

  it('returns empty array when body is null', () => {
    let response: unknown;

    service.getDevices().subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/devices/list');
    req.flush(null);

    expect(response).toEqual([]);
  });
});
