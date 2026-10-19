import 'package:vigia_ui/domain/DTOs/device_clip.dart';
import 'package:vigia_ui/domain/api_asset_url.dart';
import 'package:vigia_ui/domain/enums/clip_status.dart';

class DeviceClipUi {
  const DeviceClipUi({
    required this.id,
    required this.deviceId,
    required this.status,
    required this.frameCount,
    required this.fps,
    required this.createdAt,
    this.thumbnailUrl,
    this.playbackUrl,
  });

  final String id;
  final String deviceId;
  final ClipStatus status;
  final int frameCount;
  final int fps;
  final DateTime? createdAt;
  final String? thumbnailUrl;
  final String? playbackUrl;

  bool get isReady => status == ClipStatus.ready;

  bool get isPending =>
      status == ClipStatus.receiving || status == ClipStatus.assembling;

  /// Approximate length as m:ss from the frame count and fps.
  String? get durationLabel {
    if (fps <= 0) return null;

    final total = (frameCount / fps).round().clamp(0, 1 << 30);
    final minutes = total ~/ 60;
    final seconds = total % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }

  factory DeviceClipUi.fromDto(DeviceClip clip) {
    return DeviceClipUi(
      id: clip.id,
      deviceId: clip.deviceId,
      status: clip.status,
      frameCount: clip.frameCount,
      fps: clip.fps,
      createdAt: clip.createdAt,
      thumbnailUrl: resolveApiAssetUrl(clip.thumbnailUrl),
      playbackUrl: resolveApiAssetUrl(clip.playbackUrl),
    );
  }
}
