import 'package:vigia_ui/domain/enums/clip_status.dart';

class DeviceClip {
  const DeviceClip({
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

  factory DeviceClip.fromJson(Map<String, dynamic> json) {
    return DeviceClip(
      id: json['id'].toString(),
      deviceId: json['deviceId'].toString(),
      status: ClipStatusParsing.fromApi(json['status'] as String?),
      frameCount: (json['frameCount'] as num?)?.toInt() ?? 0,
      fps: (json['fps'] as num?)?.toInt() ?? 0,
      createdAt: DateTime.tryParse(json['createdAt'] as String? ?? ''),
      thumbnailUrl: json['thumbnailUrl'] as String?,
      playbackUrl: json['playbackUrl'] as String?,
    );
  }
}
