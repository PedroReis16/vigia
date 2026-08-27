import { FormControl, FormGroup } from '@angular/forms';
import {
  EMAIL_PATTERN,
  passwordsMatchValidator,
  requiredTrimmed,
} from './auth.validators';

describe('auth.validators', () => {
  describe('EMAIL_PATTERN', () => {
    it('accepts common emails', () => {
      expect(EMAIL_PATTERN.test('user@vigia.com')).toBe(true);
      expect(EMAIL_PATTERN.test('a.b-c@mail.co')).toBe(true);
      expect(EMAIL_PATTERN.test('user+tag@gmail.com')).toBe(true);
      expect(EMAIL_PATTERN.test('user@mail.museum')).toBe(true);
    });

    it('rejects invalid emails', () => {
      expect(EMAIL_PATTERN.test('')).toBe(false);
      expect(EMAIL_PATTERN.test('not-an-email')).toBe(false);
      expect(EMAIL_PATTERN.test('a@b')).toBe(false);
    });
  });

  describe('requiredTrimmed', () => {
    const validator = requiredTrimmed();

    it('fails for empty or whitespace-only values', () => {
      expect(validator(new FormControl(''))).toEqual({ required: true });
      expect(validator(new FormControl('   '))).toEqual({ required: true });
      expect(validator(new FormControl(null))).toEqual({ required: true });
    });

    it('passes for non-empty trimmed strings', () => {
      expect(validator(new FormControl('Ana'))).toBeNull();
      expect(validator(new FormControl('  Ana  '))).toBeNull();
    });
  });

  describe('passwordsMatchValidator', () => {
    it('returns null when confirm is empty', () => {
      const group = new FormGroup(
        {
          password: new FormControl('password1'),
          confirmPassword: new FormControl(''),
        },
        { validators: [passwordsMatchValidator()] },
      );
      expect(group.errors).toBeNull();
    });

    it('returns mismatch when passwords differ', () => {
      const group = new FormGroup(
        {
          password: new FormControl('password1'),
          confirmPassword: new FormControl('other'),
        },
        { validators: [passwordsMatchValidator()] },
      );
      expect(group.errors).toEqual({ passwordsMismatch: true });
    });

    it('returns null when passwords match', () => {
      const group = new FormGroup(
        {
          password: new FormControl('password1'),
          confirmPassword: new FormControl('password1'),
        },
        { validators: [passwordsMatchValidator()] },
      );
      expect(group.errors).toBeNull();
    });
  });
});
