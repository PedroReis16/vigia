/** Two letters for an avatar when the user has no photo. */
export function profileInitials(name: string, email: string): string {
  const trimmedName = name.trim();
  const trimmedEmail = email.trim();
  const parts = trimmedName.split(/\s+/).filter(Boolean);
  const nameIsEmail = trimmedName.localeCompare(trimmedEmail, undefined, { sensitivity: 'accent' }) === 0;

  if (!nameIsEmail && parts.length >= 2) {
    return `${parts[0].charAt(0)}${parts[1].charAt(0)}`.toUpperCase();
  }

  if (!nameIsEmail && parts.length === 1 && parts[0].charAt(0)) {
    return parts[0].charAt(0).toUpperCase();
  }

  const local = trimmedEmail.split('@')[0] ?? '';
  return local.slice(0, 2).toUpperCase();
}
