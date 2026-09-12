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

  it('closes and sets isClosed', async () => {
    const session = new WhepLiveSession('http://example.test/live/x/whep');
    await session.close();
    expect(session.getState().isClosed).toBe(true);
  });
});
