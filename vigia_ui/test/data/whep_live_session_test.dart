import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:vigia_ui/data/services/whep_live_session.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('WhepLiveSession.handlePeerConnectionState', () {
    test('marks error when peer fails after playing', () {
      final session = WhepLiveSession(
        whepUrl: 'http://example.test/live/x/whep',
      );
      session.status = WhepLiveStatus.playing;

      session.handlePeerConnectionState(
        RTCPeerConnectionState.RTCPeerConnectionStateFailed,
        generation: 0,
      );

      expect(session.status, WhepLiveStatus.error);
      expect(session.errorMessage, contains('WebRTC connection failed'));
    });

    test('ignores failure while still connecting', () {
      final session = WhepLiveSession(
        whepUrl: 'http://example.test/live/x/whep',
      );
      expect(session.status, WhepLiveStatus.connecting);

      session.handlePeerConnectionState(
        RTCPeerConnectionState.RTCPeerConnectionStateFailed,
        generation: 0,
      );

      expect(session.status, WhepLiveStatus.connecting);
      expect(session.errorMessage, isNull);
    });
  });

  group('WhepLiveSession.close', () {
    test('marks isClosed synchronously and is idempotent', () async {
      final session = WhepLiveSession(whepUrl: 'http://example.test/live/x/whep');

      expect(session.isClosed, isFalse);

      final closing = session.close();
      // Critical for navigation: UI must drop RTCVideoView before the first
      // await of teardown, otherwise dispose races the texture and freezes.
      expect(session.isClosed, isTrue);
      expect(session.status, WhepLiveStatus.connecting);

      await closing;
      await session.close();
      expect(session.isClosed, isTrue);
    });

    test('notifies listeners when close begins', () async {
      final session = WhepLiveSession(whepUrl: 'http://example.test/live/x/whep');
      var notifications = 0;
      session.addListener(() => notifications++);

      await session.close();

      expect(notifications, greaterThanOrEqualTo(1));
      expect(session.isClosed, isTrue);
    });
  });
}
