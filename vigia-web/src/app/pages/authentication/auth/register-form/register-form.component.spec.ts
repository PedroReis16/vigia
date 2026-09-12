import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { AuthErrorCode } from '@core/enums';
import { AuthUseCaseError, RegisterService } from '@core/usecases';
import { AuthSessionService, MessageService, PendingInviteService } from '@core/services';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { RegisterFormComponent } from './register-form.component';

describe('RegisterFormComponent', () => {
  let component: RegisterFormComponent;
  let fixture: ComponentFixture<RegisterFormComponent>;
  let register: { execute: ReturnType<typeof vi.fn> };
  let session: { isAuthenticated: ReturnType<typeof vi.fn> };
  let messageService: MessageService;
  let router: Router;
  let pendingInvite: { getPostAuthPath: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    register = { execute: vi.fn().mockResolvedValue(undefined) };
    session = { isAuthenticated: vi.fn().mockReturnValue(true) };
    pendingInvite = { getPostAuthPath: vi.fn().mockReturnValue('/devices') };
    vi.useFakeTimers();

    await TestBed.configureTestingModule({
      imports: [RegisterFormComponent, TranslateModule.forRoot()],
      providers: [
        { provide: RegisterService, useValue: register },
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

    fixture = TestBed.createComponent(RegisterFormComponent);
    component = fixture.componentInstance;
    messageService = TestBed.inject(MessageService);
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    fixture.detectChanges();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('submits valid registration through register use case', async () => {
    component.form.setValue({
      name: 'Ana Silva',
      email: 'ana@vigia.com',
      password: 'password1',
      confirmPassword: 'password1',
    });
    const submit = component.onSubmit();
    await vi.runAllTimersAsync();
    await submit;
    expect(register.execute).toHaveBeenCalledWith({
      name: 'Ana Silva',
      email: 'ana@vigia.com',
      password: 'password1',
    });
    expect(router.navigateByUrl).toHaveBeenCalledWith('/devices');
  });

  it('navigates to pending invite after registration', async () => {
    pendingInvite.getPostAuthPath.mockReturnValue('/invite/pending-token');
    component.form.setValue({
      name: 'Ana Silva',
      email: 'ana@vigia.com',
      password: 'password1',
      confirmPassword: 'password1',
    });
    const submit = component.onSubmit();
    await vi.runAllTimersAsync();
    await submit;
    expect(router.navigateByUrl).toHaveBeenCalledWith('/invite/pending-token');
  });

  it('trims name before calling register use case', async () => {
    component.form.setValue({
      name: '  Ana  ',
      email: 'ana@vigia.com',
      password: 'password1',
      confirmPassword: 'password1',
    });
    const submit = component.onSubmit();
    await vi.runAllTimersAsync();
    await submit;
    expect(register.execute).toHaveBeenCalledWith({
      name: 'Ana',
      email: 'ana@vigia.com',
      password: 'password1',
    });
  });

  it('does not submit when passwords mismatch', async () => {
    component.form.setValue({
      name: 'Ana',
      email: 'ana@vigia.com',
      password: 'password1',
      confirmPassword: 'other',
    });
    await component.onSubmit();
    expect(register.execute).not.toHaveBeenCalled();
  });

  it('does not submit whitespace-only name', async () => {
    component.form.setValue({
      name: '   ',
      email: 'ana@vigia.com',
      password: 'password1',
      confirmPassword: 'password1',
    });
    await component.onSubmit();
    expect(register.execute).not.toHaveBeenCalled();
  });

  it('shows error message when register use case fails', async () => {
    register.execute.mockRejectedValue(
      new AuthUseCaseError(
        'AUTH.ERRORS.EMAIL_IN_USE',
        AuthErrorCode.UserEmailAlreadyInUse,
        400,
      ),
    );
    component.form.setValue({
      name: 'Ana',
      email: 'ana@vigia.com',
      password: 'password1',
      confirmPassword: 'password1',
    });

    await component.onSubmit();

    expect(messageService.getMessages()()?.type).toBe('error');
    expect(messageService.getMessages()()?.message).toBe(
      'AUTH.ERRORS.EMAIL_IN_USE',
    );
    expect(router.navigateByUrl).not.toHaveBeenCalled();
  });
});
