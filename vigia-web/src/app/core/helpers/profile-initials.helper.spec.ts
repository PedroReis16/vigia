import { profileInitials } from './profile-initials.helper';

describe('profileInitials', () => {
  it('uses the first letter of the first and last name', () => {
    expect(profileInitials('Ana Lima', 'ana@vigia.test')).toBe('AL');
  });

  it('uses the mailbox when the display name is the email', () => {
    expect(profileInitials('ana@vigia.test', 'ana@vigia.test')).toBe('AN');
  });
});
