import {
  Component,
  DestroyRef,
  Input,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { startWith } from 'rxjs';

@Component({
  selector: 'app-auth-float-field',
  standalone: true,
  imports: [ReactiveFormsModule, TranslateModule],
  templateUrl: './auth-float-field.component.html',
  styleUrl: './auth-float-field.component.css',
})
export class AuthFloatFieldComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  @Input({ required: true }) control!: FormControl<string>;
  @Input() id = '';
  @Input() label = '';
  @Input() type: 'text' | 'password' = 'text';
  /** PrimeIcons class, e.g. `pi pi-envelope`. */
  @Input() icon = '';
  @Input() autocomplete = '';

  readonly focused = signal(false);
  readonly passwordVisible = signal(false);
  private readonly filled = signal(false);

  readonly isFloating = computed(() => this.focused() || this.filled());

  ngOnInit(): void {
    this.control.valueChanges
      .pipe(startWith(this.control.value), takeUntilDestroyed(this.destroyRef))
      .subscribe((value) => {
        this.filled.set(typeof value === 'string' ? value.length > 0 : !!value);
      });
  }

  get inputType(): string {
    if (this.type !== 'password') {
      return 'text';
    }
    return this.passwordVisible() ? 'text' : 'password';
  }

  onFocus(): void {
    this.focused.set(true);
  }

  onBlur(): void {
    this.focused.set(false);
    this.control.markAsTouched();
  }

  /** Chrome autofill often skips `input`; sync on change as well. */
  onDomChange(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    if (this.control.value !== value) {
      this.control.setValue(value);
      this.control.markAsDirty();
    }
    this.filled.set(value.length > 0);
  }

  togglePasswordVisibility(event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    this.passwordVisible.update((visible) => !visible);
  }
}
