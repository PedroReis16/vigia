import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { AuthErrorCode } from '@core/enums';
import { AuthUseCaseError, LoginService } from '@core/usecases';
import { MessageService } from '@core/services';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let login: { execute: ReturnType<typeof vi.fn> };
  let messageService: MessageService;

  beforeEach(async () => {
    login = { execute: vi.fn().mockResolvedValue(undefined) };

    await TestBed.configureTestingModule({
      imports: [LoginComponent, TranslateModule.forRoot()],
      providers: [
        { provide: LoginService, useValue: login },
        MessageService,
        provideRouter([{ path: 'devices', children: [] }]),
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: '.vigia-dark' },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    messageService = TestBed.inject(MessageService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('submits valid credentials through login use case', async () => {
    component.form.setValue({ email: 'user@vigia.com', password: 'secret' });
    await component.onSubmit();
    expect(login.execute).toHaveBeenCalledWith({
      email: 'user@vigia.com',
      password: 'secret',
    });
  });

  it('does not submit invalid form', async () => {
    component.form.setValue({ email: '', password: '' });
    await component.onSubmit();
    expect(login.execute).not.toHaveBeenCalled();
  });

  it('shows error message when login use case fails', async () => {
    login.execute.mockRejectedValue(
      new AuthUseCaseError('AUTH.ERRORS.INVALID_CREDENTIALS', AuthErrorCode.UnknownError, 401),
    );
    component.form.setValue({ email: 'user@vigia.com', password: 'wrong' });

    await component.onSubmit();

    expect(messageService.getMessages()()?.type).toBe('error');
    expect(messageService.getMessages()()?.message).toBe('AUTH.ERRORS.INVALID_CREDENTIALS');
  });
});
