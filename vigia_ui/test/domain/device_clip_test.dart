import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/device_clip.dart';
import 'package:vigia_ui/domain/enums/clip_status.dart';
import 'package:vigia_ui/domain/ui_models/device_clip_ui.dart';

void main() {
  setUpAll(() {
    dotenv.loadFromString(envString: 'API_URL=http://localhost:81/vigia');
  });

  group('DeviceClip.fromJson', () {
    test('parses a ready clip and keeps relative media paths', () {
      final clip = DeviceClip.fromJson({
        'id': 'clip-1',
        'deviceId': 'device-1',
        'status': 'Ready',
        'frameCount': 90,
        'fps': 30,
        'createdAt': '2026-10-06T15:04:00.000Z',
        'thumbnailUrl':
            'devices/device-1/clips/clip-1/thumbnail?accessToken=tok',
        'playbackUrl': 'devices/device-1/clips/clip-1?accessToken=tok',
      });

      expect(clip.status, ClipStatus.ready);
      expect(clip.frameCount, 90);
      expect(clip.fps, 30);
      expect(clip.createdAt, DateTime.utc(2026, 10, 6, 15, 4));
      expect(
        clip.thumbnailUrl,
        'devices/device-1/clips/clip-1/thumbnail?accessToken=tok',
      );
      expect(clip.playbackUrl, 'devices/device-1/clips/clip-1?accessToken=tok');
    });

    test('maps an unknown status to failed and leaves media empty', () {
      final clip = DeviceClip.fromJson({
        'id': 'clip-2',
        'deviceId': 'device-1',
        'status': 'Broken',
        'createdAt': 'not-a-date',
      });

      expect(clip.status, ClipStatus.failed);
      expect(clip.frameCount, 0);
      expect(clip.fps, 0);
      expect(clip.createdAt, isNull);
      expect(clip.thumbnailUrl, isNull);
      expect(clip.playbackUrl, isNull);
    });
  });

  group('DeviceClipUi', () {
    test('resolves relative urls and the duration label', () {
      final clip = DeviceClipUi.fromDto(
        DeviceClip.fromJson({
          'id': 'clip-1',
          'deviceId': 'device-1',
          'status': 'Ready',
          'frameCount': 90,
          'fps': 30,
          'createdAt': '2026-10-06T15:04:00.000Z',
          'thumbnailUrl':
              'devices/device-1/clips/clip-1/thumbnail?accessToken=tok',
          'playbackUrl': 'devices/device-1/clips/clip-1?accessToken=tok',
        }),
      );

      expect(clip.isReady, isTrue);
      expect(clip.isPending, isFalse);
      expect(clip.durationLabel, '0:03');
      expect(
        clip.thumbnailUrl,
        'http://localhost:81/vigia/devices/device-1/clips/clip-1/thumbnail?accessToken=tok',
      );
      expect(
        clip.playbackUrl,
        'http://localhost:81/vigia/devices/device-1/clips/clip-1?accessToken=tok',
      );
    });

    test('keeps a pending clip without media', () {
      final clip = DeviceClipUi.fromDto(
        DeviceClip.fromJson({
          'id': 'clip-3',
          'deviceId': 'device-1',
          'status': 'Receiving',
          'frameCount': 0,
          'fps': 0,
          'createdAt': '2026-10-06T15:04:00.000Z',
        }),
      );

      expect(clip.isPending, isTrue);
      expect(clip.isReady, isFalse);
      expect(clip.durationLabel, isNull);
      expect(clip.thumbnailUrl, isNull);
      expect(clip.playbackUrl, isNull);
    });

    test('preserves an absolute playback url', () {
      final clip = DeviceClipUi.fromDto(
        const DeviceClip(
          id: 'clip-4',
          deviceId: 'device-1',
          status: ClipStatus.assembling,
          frameCount: 120,
          fps: 30,
          createdAt: null,
          playbackUrl: 'https://cdn.example/clip.mp4',
        ),
      );

      expect(clip.isPending, isTrue);
      expect(clip.durationLabel, '0:04');
      expect(clip.playbackUrl, 'https://cdn.example/clip.mp4');
    });
  });
}
