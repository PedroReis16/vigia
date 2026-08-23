import { describe, expect, it } from 'vitest';
import { resolveApiAssetUrl } from './api-asset-url.helper';
import { environment } from '@environments/environment';

describe('resolveApiAssetUrl', () => {
  it('returns null for empty paths', () => {
    expect(resolveApiAssetUrl(null)).toBeNull();
    expect(resolveApiAssetUrl('')).toBeNull();
    expect(resolveApiAssetUrl('   ')).toBeNull();
  });

  it('keeps absolute URLs', () => {
    expect(resolveApiAssetUrl('https://cdn.example/pic.jpg')).toBe(
      'https://cdn.example/pic.jpg',
    );
  });

  it('prefixes relative paths with apiUrl', () => {
    const apiBase = environment.apiUrl.replace(/\/$/, '');
    expect(resolveApiAssetUrl('pictures/a.jpg')).toBe(`${apiBase}/pictures/a.jpg`);
    expect(resolveApiAssetUrl('/pictures/a.jpg')).toBe(`${apiBase}/pictures/a.jpg`);
  });
});
