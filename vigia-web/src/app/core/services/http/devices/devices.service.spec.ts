import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { DevicesService } from './devices.service';
import { DeviceRooms } from '@core/enums';

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

  it('gets a single device', () => {
    let response: unknown;

    service.getDevice('device-1').subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/devices/device-1');
    expect(req.request.method).toBe('GET');
    req.flush({
      id: 'device-1',
      name: 'Vigia-test',
      nickname: 'Quarto',
      room: 'Bedroom',
      ownerId: 'u1',
      macAddress: 'AA:BB',
      isRunning: true,
      isClipsEnabled: false,
    });

    expect(response).toEqual(expect.objectContaining({ id: 'device-1', nickname: 'Quarto' }));
  });

  it('returns null for single device 204', () => {
    let response: unknown;

    service.getDevice('missing').subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/devices/missing');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(response).toBeNull();
  });

  it('updates device', () => {
    service
      .updateDevice('device-1', { nickname: 'New', room: DeviceRooms.Kitchen, isClipsEnabled: true })
      .subscribe();

    const req = httpMock.expectOne('/devices/device-1');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({
      nickname: 'New',
      room: DeviceRooms.Kitchen,
      isClipsEnabled: true,
    });
    req.flush(null);
  });

  it('sends streaming command', () => {
    service.sendCommand('device-1', 'START_STREAMING').subscribe();

    const req = httpMock.expectOne('/devices/device-1/command');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ command: 'START_STREAMING', commandValue: '' });
    req.flush(null);
  });

  it('gets device users', () => {
    let response: unknown;

    service.getDeviceUsers('device-1').subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/devices/device-1/users');
    req.flush([{ id: 'u1', name: 'Owner', isOwner: true }]);

    expect(response).toEqual([{ id: 'u1', name: 'Owner', isOwner: true }]);
  });

  it('generates share link', () => {
    let response: unknown;

    service.generateShareLink('device-1').subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/devices/device-1/share/generate');
    req.flush({
      token: 'abc',
      inviteUrl: 'https://example.com/invite/abc',
      expiresAt: '2026-01-01T00:00:00Z',
    });

    expect(response).toEqual(
      expect.objectContaining({ token: 'abc', inviteUrl: 'https://example.com/invite/abc' }),
    );
  });

  it('removes device user', () => {
    service.removeDeviceUser('device-1', 'user-2').subscribe();

    const req = httpMock.expectOne('/devices/device-1/users/user-2');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('accepts share invite', () => {
    service.acceptShareInvite('invite-token').subscribe();

    const req = httpMock.expectOne('/devices/share/accept');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ token: 'invite-token' });
    req.flush(null);
  });
});
