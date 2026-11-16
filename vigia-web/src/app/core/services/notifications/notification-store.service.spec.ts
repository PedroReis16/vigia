import { TestBed } from '@angular/core/testing';
import { FallNotification } from '@core/entities/classes/fall-notification';
import { NotificationStoreService } from './notification-store.service';

describe('NotificationStoreService', () => {
  let service: NotificationStoreService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [NotificationStoreService],
    });

    service = TestBed.inject(NotificationStoreService);
  });

  it('starts empty', () => {
    expect(service.notifications()).toEqual([]);
    expect(service.unreadCount()).toBe(0);
  });

  it('replaces inbox from API payload', () => {
    service.replaceAll([createNotification('1'), createNotification('2', true)], 1);

    expect(service.notifications()).toHaveLength(2);
    expect(service.unreadCount()).toBe(1);
  });

  it('upserts without duplicating episode', () => {
    service.replaceAll([createNotification('server-1')], 1);
    service.upsert({
      ...createNotification('optimistic'),
      episodeId: 'episode-1',
    });

    expect(service.notifications()).toHaveLength(1);
    expect(service.notifications()[0]?.id).toBe('optimistic');
    expect(service.unreadCount()).toBe(1);
  });

  it('marks a notification as read', () => {
    service.replaceAll([createNotification('1')], 1);
    service.markRead('1');

    expect(service.unreadCount()).toBe(0);
    expect(service.notifications()[0]?.read).toBe(true);
  });

  it('clears notifications on logout', () => {
    service.replaceAll([createNotification('1')], 1);
    service.clearForLogout();

    expect(service.notifications()).toEqual([]);
    expect(service.unreadCount()).toBe(0);
  });
});

function createNotification(id: string, read = false): FallNotification {
  return {
    id,
    episodeId: 'episode-1',
    type: 'fall',
    deviceId: `device-${id}`,
    deviceName: `Device ${id}`,
    nickname: '',
    title: 'Alerta de queda',
    body: `Queda detectada em Device ${id}`,
    receivedAt: new Date().toISOString(),
    read,
  };
}
