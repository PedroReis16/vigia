import { computeEnterRevealClip } from './element-bounds.helper';

describe('computeEnterRevealClip', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 800 });
    Object.defineProperty(window, 'innerHeight', { configurable: true, value: 600 });
  });

  it('returns hidden clip at zero progress', () => {
    expect(
      computeEnterRevealClip({ top: 100, left: 50, width: 200, height: 120 }, 0),
    ).toEqual({
      cx: 150,
      cy: 160,
      rx: 0,
      ry: 0,
      opacity: 0,
    });
  });

  it('expands ellipse toward viewport edges at full progress', () => {
    const clip = computeEnterRevealClip({ top: 100, left: 50, width: 200, height: 120 }, 1);

    expect(clip.cx).toBe(150);
    expect(clip.cy).toBe(160);
    expect(clip.rx).toBeGreaterThan(600);
    expect(clip.ry).toBeGreaterThan(440);
    expect(clip.opacity).toBe(1);
  });
});
