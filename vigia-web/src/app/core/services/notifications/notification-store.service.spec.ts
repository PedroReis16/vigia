import { TestBed } from '@angular/core/testing';
import { FallNotification } from '@core/entities/classes/fall-notification';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { NotificationStoreService } from './notification-store.service';

describe('NotificationStoreService', () => {
  let service: NotificationStoreService;
  let session: { getUserId: ReturnType<typeof vi.fn> };
  const storage = new Map<string, string>();

  beforeEach(() => {
    storage.clear();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
      clear: () => {
        storage.clear();
      },
    });

    session = { getUserId: vi.fn(() => 'user-1') };

    TestBed.configureTestingModule({
      providers: [
        NotificationStoreService,
        { provide: AuthSessionService, useValue: session },
      ],
    });

    service = TestBed.inject(NotificationStoreService);
    service.bindToCurrentUser();
  });

  it('starts empty', () => {
    expect(service.notifications()).toEqual([]);
    expect(service.unreadCount()).toBe(0);
  });

  it('adds notifications and tracks unread count', () => {
    const notification = createNotification('1');

    service.add(notification);

    expect(service.notifications()).toHaveLength(1);
    expect(service.unreadCount()).toBe(1);
  });

  it('marks a notification as read', () => {
    const notification = createNotification('1');
    service.add(notification);

    service.markRead(notification.id);

    expect(service.unreadCount()).toBe(0);
    expect(service.notifications()[0]?.read).toBe(true);
  });

  it('persists and restores notifications for the current user', () => {
    service.add(createNotification('1'));

    expect(localStorage.getItem('vigia:notifications:user-1')).toBeTruthy();

    service.clearForLogout();
    service.bindToCurrentUser();

    expect(service.notifications()).toHaveLength(1);
    expect(service.notifications()[0]?.deviceId).toBe('device-1');
  });

  it('caps stored notifications at 50 items', () => {
    for (let index = 0; index < 55; index += 1) {
      service.add(createNotification(String(index)));
    }

    expect(service.notifications()).toHaveLength(50);
  });

  it('clears notifications on logout', () => {
    service.add(createNotification('1'));
    service.clearForLogout();

    expect(service.notifications()).toEqual([]);
    expect(service.unreadCount()).toBe(0);
  });
});

function createNotification(id: string): FallNotification {
  return {
    id,
    type: 'fall',
    deviceId: `device-${id}`,
    deviceName: `Device ${id}`,
    nickname: '',
    title: 'Alerta de queda',
    body: `Queda detectada em Device ${id}`,
    receivedAt: new Date().toISOString(),
    read: false,
  };
}
