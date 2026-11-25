import { WhepLiveSession } from '@core/services';

describe('WhepLiveSession', () => {
  it('starts in connecting state', () => {
    const session = new WhepLiveSession('http://example.test/live/x/whep');
    expect(session.getState().status).toBe('connecting');
  });

  it('marks error', () => {
    const session = new WhepLiveSession('http://example.test/live/x/whep');
    session.markError(new Error('boom'));
    expect(session.getState().status).toBe('error');
    expect(session.getState().errorMessage).toBe('boom');
  });

  it('marks error when peer fails after playing', () => {
    const session = new WhepLiveSession('http://example.test/live/x/whep');
    session.beginConnecting();
    // Simulate post-WHEP playing without a real peer.
    (session as unknown as { status: string }).status = 'playing';
    session.handlePeerConnectionState('failed', 0);
    expect(session.getState().status).toBe('error');
    expect(session.getState().errorMessage).toBe('WebRTC connection failed');
  });

  it('ignores peer failure while still connecting', () => {
    const session = new WhepLiveSession('http://example.test/live/x/whep');
    session.handlePeerConnectionState('failed', 0);
    expect(session.getState().status).toBe('connecting');
    expect(session.getState().errorMessage).toBeNull();
  });

  it('closes and sets isClosed', async () => {
    const session = new WhepLiveSession('http://example.test/live/x/whep');
    await session.close();
    expect(session.getState().isClosed).toBe(true);
  });
});
