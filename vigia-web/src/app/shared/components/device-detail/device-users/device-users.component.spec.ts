import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { Subject } from 'rxjs';
import { vi } from 'vitest';
import { DeviceShareInvite, DeviceUser, GroupMembershipChangedDto } from '@core/entities';
import { AuthSessionService, DeviceGroupsRealtimeService, MessageService } from '@core/services';
import {
  GenerateDeviceShareLinkService,
  GetDeviceUsersService,
  RemoveDeviceUserService,
} from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { DeviceUsersComponent } from './device-users.component';

describe('DeviceUsersComponent', () => {
  let component: DeviceUsersComponent;
  let fixture: ComponentFixture<DeviceUsersComponent>;
  let getDeviceUsers: { execute: ReturnType<typeof vi.fn> };
  let generateShareLink: { execute: ReturnType<typeof vi.fn> };
  const membershipChanged$ = new Subject<GroupMembershipChangedDto>();

  const users = [
    new DeviceUser('u1', 'Owner', null, true),
    new DeviceUser('u2', 'Guest', null, false),
  ];

  beforeEach(async () => {
    getDeviceUsers = { execute: vi.fn().mockResolvedValue(users) };
    generateShareLink = { execute: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [DeviceUsersComponent, TranslateModule.forRoot()],
      providers: [
        { provide: GetDeviceUsersService, useValue: getDeviceUsers },
        { provide: GenerateDeviceShareLinkService, useValue: generateShareLink },
        {
          provide: DeviceGroupsRealtimeService,
          useValue: { membershipChanged$: membershipChanged$.asObservable() },
        },
        { provide: RemoveDeviceUserService, useValue: { execute: vi.fn() } },
        { provide: AuthSessionService, useValue: { getUserId: () => 'u1' } },
        MessageService,
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DeviceUsersComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('deviceId', 'device-1');
    fixture.componentRef.setInput('isOwner', true);
  });

  it('loads and renders users', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(getDeviceUsers.execute).toHaveBeenCalledWith('device-1');
    expect(component.users()).toEqual(users);
    expect(component.loading()).toBe(false);
    expect(fixture.nativeElement.querySelector('[data-testid="device-users-list"]')).toBeTruthy();
  });

  it('shows error state and retries', async () => {
    getDeviceUsers.execute.mockRejectedValueOnce(new Error('fail'));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.error()).toBe(true);
    expect(fixture.nativeElement.querySelector('[data-testid="device-users-error"]')).toBeTruthy();

    getDeviceUsers.execute.mockResolvedValueOnce(users);
    await component.onRetry();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[data-testid="device-users-list"]')).toBeTruthy();
  });

  it('reloads users when the open device membership changes', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    expect(getDeviceUsers.execute).toHaveBeenCalledTimes(1);

    membershipChanged$.next({
      groupId: 'group-1',
      affectedUserId: 'u2',
      changeType: 'joined',
      deviceIds: ['device-1'],
    });
    await fixture.whenStable();

    expect(getDeviceUsers.execute).toHaveBeenCalledTimes(2);
  });

  it('shows the generated link and its expiry', async () => {
    generateShareLink.execute.mockResolvedValue(
      new DeviceShareInvite('tok', 'https://services.example/vigia/i/tok', new Date('2026-10-15T23:05:00Z')),
    );
    const share = vi.fn();
    vi.stubGlobal('navigator', {
      ...navigator,
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
      share,
    });

    fixture.detectChanges();
    await fixture.whenStable();
    await component.onShare();
    fixture.detectChanges();

    const link = fixture.nativeElement.querySelector('[data-testid="device-share-link"]');
    const input = fixture.nativeElement.querySelector(
      '[data-testid="device-share-link-input"]',
    ) as HTMLInputElement;
    expect(input.value).toBe('https://services.example/vigia/i/tok');
    expect(link?.textContent).toContain('DEVICES.USERS.SHARE_EXPIRES');
    expect(link?.textContent).toContain('DEVICES.USERS.SHARE_COPY');

    const copy = fixture.nativeElement.querySelector('[data-testid="device-share-copy"]') as HTMLButtonElement;
    copy.click();
    await fixture.whenStable();
    copy.click();
    await fixture.whenStable();

    expect(generateShareLink.execute).toHaveBeenCalledTimes(1);
    expect(navigator.clipboard.writeText).toHaveBeenCalledTimes(3);
    expect(share).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});
