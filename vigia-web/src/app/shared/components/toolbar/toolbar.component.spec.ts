import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { FallNotification, UserProfile } from '@core/entities';
import { AuthExitTransitionService, MessageService, NotificationStoreService, UserProfileStoreService } from '@core/services';
import {
  GetUserProfileService,
  LoadNotificationsService,
  LogoutService,
  MarkAllNotificationsReadService,
  MarkNotificationReadService,
  NavigateToFallAlertService,
  SyncPushNotificationsService,
} from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { ToolbarComponent } from './toolbar.component';

describe('ToolbarComponent', () => {
  let component: ToolbarComponent;
  let fixture: ComponentFixture<ToolbarComponent>;
  let logout: { execute: ReturnType<typeof vi.fn> };
  let navigateToFallAlert: { execute: ReturnType<typeof vi.fn> };
  let syncPushNotifications: { execute: ReturnType<typeof vi.fn> };
  let markNotificationRead: { execute: ReturnType<typeof vi.fn> };
  let profileStore: UserProfileStoreService;
  let authExitTransition: AuthExitTransitionService;
  let notificationStore: {
    notifications: ReturnType<typeof signal<FallNotification[]>>;
    unreadCount: ReturnType<typeof signal<number>>;
    markRead: ReturnType<typeof vi.fn>;
    markAllRead: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    logout = { execute: vi.fn().mockResolvedValue(undefined) };
    navigateToFallAlert = { execute: vi.fn().mockResolvedValue(true) };
    syncPushNotifications = { execute: vi.fn().mockResolvedValue(true) };
    markNotificationRead = { execute: vi.fn().mockResolvedValue(undefined) };
    notificationStore = {
      notifications: signal<FallNotification[]>([]),
      unreadCount: signal(0),
      markRead: vi.fn(),
      markAllRead: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ToolbarComponent, TranslateModule.forRoot()],
      providers: [
        { provide: LogoutService, useValue: logout },
        { provide: NavigateToFallAlertService, useValue: navigateToFallAlert },
        { provide: SyncPushNotificationsService, useValue: syncPushNotifications },
        { provide: LoadNotificationsService, useValue: { execute: vi.fn().mockResolvedValue(undefined) } },
        { provide: MarkNotificationReadService, useValue: markNotificationRead },
        { provide: MarkAllNotificationsReadService, useValue: { execute: vi.fn().mockResolvedValue(undefined) } },
        { provide: GetUserProfileService, useValue: { execute: vi.fn().mockResolvedValue(undefined) } },
        { provide: NotificationStoreService, useValue: notificationStore },
        MessageService,
        provideRouter([
          { path: 'login', children: [] },
          { path: 'devices/:deviceId', children: [] },
          { path: 'profile', children: [] },
        ]),
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ToolbarComponent);
    component = fixture.componentInstance;
    authExitTransition = TestBed.inject(AuthExitTransitionService);
    profileStore = TestBed.inject(UserProfileStoreService);
    authExitTransition.complete();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render logo, notifications trigger and user menu trigger', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="toolbar-logo"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="notifications-trigger"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="user-menu-trigger"]')).toBeTruthy();
  });

  it('should show unread badge when there are unread notifications', () => {
    notificationStore.unreadCount.set(2);
    fixture.detectChanges();

    const badge = fixture.nativeElement.querySelector('[data-testid="notifications-badge"]');
    expect(badge?.textContent?.trim()).toBe('2');
  });

  it('should navigate when a notification is clicked', async () => {
    const notification: FallNotification = {
      id: '1',
      type: 'fall',
      deviceId: 'device-1',
      deviceName: 'Vigia-abc',
      nickname: '',
      title: 'Alerta de queda',
      body: 'Queda detectada',
      receivedAt: new Date().toISOString(),
      read: false,
    };

    await component.onNotificationClick(notification);

    expect(notificationStore.markRead).not.toHaveBeenCalled();
    expect(markNotificationRead.execute).toHaveBeenCalledWith('1');
    expect(navigateToFallAlert.execute).toHaveBeenCalledWith({
      type: 'fall',
      deviceId: 'device-1',
      alertId: undefined,
    });
  });

  it('should logout via use case', async () => {
    vi.spyOn(authExitTransition, 'waitForShellExit').mockResolvedValue(undefined);
    await component.onLogout();
    expect(logout.execute).toHaveBeenCalled();
  });

  it('arms logout transition before ending the session', async () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const toolbar = compiled.querySelector('[data-testid="app-toolbar"]') as HTMLElement;
    const logo = compiled.querySelector('[data-testid="toolbar-logo"] img') as HTMLElement;

    Object.defineProperty(toolbar, 'getBoundingClientRect', {
      value: () => ({
        top: 0,
        left: 0,
        width: 800,
        height: 80,
        right: 800,
        bottom: 80,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }),
    });
    Object.defineProperty(logo, 'getBoundingClientRect', {
      value: () => ({
        top: 12,
        left: 20,
        width: 56,
        height: 56,
        right: 76,
        bottom: 68,
        x: 20,
        y: 12,
        toJSON: () => ({}),
      }),
    });

    vi.spyOn(authExitTransition, 'waitForShellExit').mockResolvedValue(undefined);

    await component.onLogout();

    expect(authExitTransition.kind()).toBe('logout');
    expect(logout.execute).toHaveBeenCalled();
  });

  it('stores the flying logo so the next page can meet Keycloak', async () => {
    sessionStorage.removeItem('vigia.auth.exit');
    const compiled = fixture.nativeElement as HTMLElement;
    const toolbar = compiled.querySelector('[data-testid="app-toolbar"]') as HTMLElement;
    const logo = compiled.querySelector('[data-testid="toolbar-logo"] img') as HTMLElement;
    const bounds = {
      top: 0,
      left: 0,
      width: 800,
      height: 80,
      right: 800,
      bottom: 80,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    };

    Object.defineProperty(toolbar, 'getBoundingClientRect', { value: () => bounds });
    Object.defineProperty(logo, 'getBoundingClientRect', {
      value: () => ({ ...bounds, top: 12, left: 20, width: 56, height: 56, right: 76, bottom: 68 }),
    });
    vi.spyOn(authExitTransition, 'waitForShellExit').mockImplementation(async () => {
      authExitTransition.setHandoffLogo({ top: 180, left: 300, height: 225 });
    });

    await component.onLogout();

    expect(sessionStorage.getItem('vigia.auth.exit')).toBe('180,300,225,225');
    sessionStorage.removeItem('vigia.auth.exit');
  });

  it('shows the profile name and picture in the toolbar', () => {
    profileStore.set(new UserProfile(
      'user-1',
      'Ana Lima',
      'Ana',
      'Lima',
      'ana@vigia.test',
      '11999990000',
      'https://example.test/picture.jpg',
      true,
    ));
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const image = compiled.querySelector('.toolbar__avatar-btn img') as HTMLImageElement | null;
    expect(image?.getAttribute('src')).toBe('https://example.test/picture.jpg');

    component.toggleUserMenu(new MouseEvent('click'));
    fixture.detectChanges();

    const menu = document.body.querySelector('[data-testid="user-menu-profile"]');
    expect(menu?.textContent).toContain('Ana Lima');
    expect(menu?.textContent).toContain('ana@vigia.test');
    expect(document.body.querySelector('[data-testid="profile-link"]')).toBeTruthy();
  });
});
