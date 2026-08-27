import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { DeviceUser } from '@core/entities';
import { AuthSessionService, MessageService } from '@core/services';
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

  const users = [
    new DeviceUser('u1', 'Owner', null, true),
    new DeviceUser('u2', 'Guest', null, false),
  ];

  beforeEach(async () => {
    getDeviceUsers = { execute: vi.fn().mockResolvedValue(users) };

    await TestBed.configureTestingModule({
      imports: [DeviceUsersComponent, TranslateModule.forRoot()],
      providers: [
        { provide: GetDeviceUsersService, useValue: getDeviceUsers },
        { provide: GenerateDeviceShareLinkService, useValue: { execute: vi.fn() } },
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
});
