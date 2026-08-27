import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormControl } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { AuthFloatFieldComponent } from './auth-float-field.component';

describe('AuthFloatFieldComponent', () => {
  let fixture: ComponentFixture<AuthFloatFieldComponent>;
  let component: AuthFloatFieldComponent;

  async function setup(
    options: { type?: 'text' | 'password' } = {},
  ): Promise<void> {
    await TestBed.configureTestingModule({
      imports: [AuthFloatFieldComponent, TranslateModule.forRoot()],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthFloatFieldComponent);
    component = fixture.componentInstance;
    component.control = new FormControl('', { nonNullable: true });
    component.id = 'email';
    component.label = 'AUTH.FIELDS.EMAIL';
    component.type = options.type ?? 'text';
    fixture.detectChanges();
  }

  it('should create', async () => {
    await setup();
    expect(component).toBeTruthy();
  });

  it('floats label on focus and keeps it floated when value is set', async () => {
    await setup();
    const compiled = fixture.nativeElement as HTMLElement;
    const root = compiled.querySelector('.auth-float')!;

    expect(root.classList.contains('auth-float--float')).toBe(false);

    component.onFocus();
    fixture.detectChanges();
    expect(root.classList.contains('auth-float--float')).toBe(true);

    component.onBlur();
    fixture.detectChanges();
    expect(root.classList.contains('auth-float--float')).toBe(false);

    component.control.setValue('user@vigia.com');
    fixture.detectChanges();
    expect(root.classList.contains('auth-float--float')).toBe(true);
  });

  it('toggles password visibility', async () => {
    await setup({ type: 'password' });

    const button = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="auth-float-visibility"]',
    ) as HTMLButtonElement;
    expect(button).toBeTruthy();
    expect(component.inputType).toBe('password');

    button.click();
    fixture.detectChanges();
    expect(component.inputType).toBe('text');
  });
});
