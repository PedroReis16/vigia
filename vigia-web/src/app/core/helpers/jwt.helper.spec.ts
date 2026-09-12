import { readJwtSubject } from './jwt.helper';

describe('readJwtSubject', () => {
  it('reads sub from a valid JWT payload', () => {
    // {"sub":"user-42"}
    const token = `header.${btoa(JSON.stringify({ sub: 'user-42' }))}.sig`;
    expect(readJwtSubject(token)).toBe('user-42');
  });

  it('supports URL-safe base64 payloads', () => {
    const json = JSON.stringify({ sub: 'abc' });
    const urlSafe = btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    expect(readJwtSubject(`h.${urlSafe}.s`)).toBe('abc');
  });

  it('returns null when payload has no sub', () => {
    const token = `h.${btoa(JSON.stringify({ email: 'a@b.com' }))}.s`;
    expect(readJwtSubject(token)).toBeNull();
  });

  it('returns null for malformed tokens', () => {
    expect(readJwtSubject('not-a-jwt')).toBeNull();
    expect(readJwtSubject('')).toBeNull();
    expect(readJwtSubject('a.!!.c')).toBeNull();
  });
});
