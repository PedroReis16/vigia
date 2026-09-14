import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export const EMAIL_PATTERN = /^[\w.+-]+@([\w-]+\.)+[\w-]{2,}$/;

export function requiredTrimmed(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value;
    if (typeof value !== 'string' || value.trim().length === 0) {
      return { required: true };
    }
    return null;
  };
}

export function passwordsMatchValidator(
  passwordKey = 'password',
  confirmKey = 'confirmPassword',
): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const password = control.get(passwordKey)?.value as string | undefined;
    const confirm = control.get(confirmKey)?.value as string | undefined;

    if (!confirm) {
      return null;
    }

    return password === confirm ? null : { passwordsMismatch: true };
  };
}
