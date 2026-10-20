import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/enums/clip_status.dart';
import 'package:vigia_ui/domain/ui_models/device_clip_ui.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_clips.dart';

import '../../helpers/pump_app.dart';

DeviceClipUi _clip({
  required String id,
  required ClipStatus status,
  String? playbackUrl,
  int frameCount = 90,
  int fps = 30,
}) {
  return DeviceClipUi(
    id: id,
    deviceId: 'device-1',
    status: status,
    frameCount: frameCount,
    fps: fps,
    createdAt: DateTime.utc(2026, 10, 6, 15, 4),
    playbackUrl: playbackUrl,
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('shows the empty state', (tester) async {
    await pumpApp(
      tester,
      child: Scaffold(
        body: DeviceClips(clips: const [], onPlay: (_) {}),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('No fall clips yet.'), findsOneWidget);
  });

  testWidgets('shows duration and status for a ready clip', (tester) async {
    String? played;

    await pumpApp(
      tester,
      child: Scaffold(
        body: DeviceClips(
          clips: [
            _clip(
              id: 'clip-1',
              status: ClipStatus.ready,
              playbackUrl: 'https://cdn.example/clip.mp4',
            ),
          ],
          onPlay: (clip) => played = clip.id,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('0:03'), findsOneWidget);
    expect(find.text('Ready'), findsOneWidget);

    await tester.tap(find.text('Ready'));
    expect(played, 'clip-1');
  });

  testWidgets('does not play a pending clip', (tester) async {
    var played = false;

    await pumpApp(
      tester,
      child: Scaffold(
        body: DeviceClips(
          clips: [_clip(id: 'clip-2', status: ClipStatus.receiving, fps: 0)],
          onPlay: (_) => played = true,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Receiving'), findsOneWidget);
    expect(find.text('0:03'), findsNothing);

    await tester.tap(find.text('Receiving'));
    expect(played, isFalse);
  });
}
