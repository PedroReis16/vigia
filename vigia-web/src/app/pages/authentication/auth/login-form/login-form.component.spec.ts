import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { AuthErrorCode } from '@core/enums';
import { AuthUseCaseError, LoginService } from '@core/usecases';
import {
  AuthExitTransitionService,
  AuthSessionService,
  MessageService,
  PendingInviteService,
} from '@core/services';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { LoginFormComponent } from './login-form.component';

describe('LoginFormComponent', () => {
  let component: LoginFormComponent;
  let fixture: ComponentFixture<LoginFormComponent>;
  let login: { execute: ReturnType<typeof vi.fn> };
  let session: { isAuthenticated: ReturnType<typeof vi.fn> };
  let messageService: MessageService;
  let router: Router;
  let authExitTransition: AuthExitTransitionService;
  let pendingInvite: { getPostAuthPath: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    login = { execute: vi.fn().mockResolvedValue(undefined) };
    session = { isAuthenticated: vi.fn().mockReturnValue(true) };
    pendingInvite = { getPostAuthPath: vi.fn().mockReturnValue('/devices') };
    vi.useFakeTimers();

    await TestBed.configureTestingModule({
      imports: [LoginFormComponent, TranslateModule.forRoot()],
      providers: [
        { provide: LoginService, useValue: login },
        { provide: AuthSessionService, useValue: session },
        { provide: PendingInviteService, useValue: pendingInvite },
        MessageService,
        provideRouter([{ path: 'devices', children: [] }]),
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginFormComponent);
    component = fixture.componentInstance;
    messageService = TestBed.inject(MessageService);
    router = TestBed.inject(Router);
    authExitTransition = TestBed.inject(AuthExitTransitionService);
    authExitTransition.complete();
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    fixture.detectChanges();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('submits valid credentials and navigates to devices', async () => {
    component.form.setValue({ email: 'user@vigia.com', password: 'secret' });
    const submit = component.onSubmit();
    await vi.runAllTimersAsync();
    await submit;
    expect(login.execute).toHaveBeenCalledWith({
      email: 'user@vigia.com',
      password: 'secret',
    });
    expect(router.navigateByUrl).toHaveBeenCalledWith('/devices');
    expect(authExitTransition.isArmed()).toBe(true);
  });

  it('navigates to pending invite after login', async () => {
    pendingInvite.getPostAuthPath.mockReturnValue('/invite/pending-token');
    component.form.setValue({ email: 'user@vigia.com', password: 'secret' });
    const submit = component.onSubmit();
    await vi.runAllTimersAsync();
    await submit;
    expect(router.navigateByUrl).toHaveBeenCalledWith('/invite/pending-token');
  });

  it('does not submit invalid form', async () => {
    component.form.setValue({ email: '', password: '' });
    await component.onSubmit();
    expect(login.execute).not.toHaveBeenCalled();
  });

  it('enables submit when email and password are non-empty', () => {
    component.form.setValue({ email: 'not-an-email', password: 'secret' });
    expect(component.canSubmit()).toBe(true);
    expect(component.ctaDisabled()).toBe(false);
  });

  it('shows error message when login use case fails', async () => {
    login.execute.mockRejectedValue(
      new AuthUseCaseError(
        'AUTH.ERRORS.INVALID_CREDENTIALS',
        AuthErrorCode.UnknownError,
        401,
      ),
    );
    component.form.setValue({ email: 'user@vigia.com', password: 'wrong' });

    await component.onSubmit();

    expect(messageService.getMessages()()?.type).toBe('error');
    expect(messageService.getMessages()()?.message).toBe(
      'AUTH.ERRORS.INVALID_CREDENTIALS',
    );
    expect(router.navigateByUrl).not.toHaveBeenCalled();
  });

  it('shows error when session is missing after login', async () => {
    session.isAuthenticated.mockReturnValue(false);
    component.form.setValue({ email: 'user@vigia.com', password: 'secret' });

    await component.onSubmit();

    expect(messageService.getMessages()()?.type).toBe('error');
    expect(router.navigateByUrl).not.toHaveBeenCalled();
  });
});
