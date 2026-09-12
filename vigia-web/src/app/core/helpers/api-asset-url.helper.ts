import { environment } from '@environments/environment';

/** Builds an absolute URL for API-relative asset paths (e.g. device thumbnails). */
export function resolveApiAssetUrl(path: string | null | undefined): string | null {
  if (!path?.trim()) {
    return null;
  }

  const trimmed = path.trim();
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }

  const base = environment.apiUrl.replace(/\/$/, '');
  const relative = trimmed.replace(/^\//, '');
  return `${base}/${relative}`;
}
