import { TestBed } from '@angular/core/testing';
import { PendingInviteService } from './pending-invite.service';

describe('PendingInviteService', () => {
  let service: PendingInviteService;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [PendingInviteService],
    });
    service = TestBed.inject(PendingInviteService);
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it('stores and retrieves token', () => {
    service.setToken('abc123');
    expect(service.getToken()).toBe('abc123');
  });

  it('clears token', () => {
    service.setToken('abc123');
    service.clear();
    expect(service.getToken()).toBeNull();
  });

  it('returns invite path when token is pending', () => {
    service.setToken('abc123');
    expect(service.getPostAuthPath()).toBe('/invite/abc123');
  });

  it('returns devices path when no token is pending', () => {
    expect(service.getPostAuthPath()).toBe('/devices');
  });
});
