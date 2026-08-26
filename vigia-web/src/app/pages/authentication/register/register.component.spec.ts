import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { AuthErrorCode } from '@core/enums';
import { AuthUseCaseError, RegisterService } from '@core/usecases';
import { MessageService } from '@core/services';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { RegisterComponent } from './register.component';

describe('RegisterComponent', () => {
  let component: RegisterComponent;
  let fixture: ComponentFixture<RegisterComponent>;
  let register: { execute: ReturnType<typeof vi.fn> };
  let messageService: MessageService;

  beforeEach(async () => {
    register = { execute: vi.fn().mockResolvedValue(undefined) };

    await TestBed.configureTestingModule({
      imports: [RegisterComponent, TranslateModule.forRoot()],
      providers: [
        { provide: RegisterService, useValue: register },
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

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    messageService = TestBed.inject(MessageService);
    fixture.detectChanges();
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
    await component.onSubmit();
    expect(register.execute).toHaveBeenCalledWith({
      name: 'Ana Silva',
      email: 'ana@vigia.com',
      password: 'password1',
    });
  });

  it('trims name before calling register use case', async () => {
    component.form.setValue({
      name: '  Ana  ',
      email: 'ana@vigia.com',
      password: 'password1',
      confirmPassword: 'password1',
    });
    await component.onSubmit();
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
    expect(messageService.getMessages()()?.message).toBe('AUTH.ERRORS.EMAIL_IN_USE');
  });
});
