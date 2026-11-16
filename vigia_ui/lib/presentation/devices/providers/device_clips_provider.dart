import 'dart:async';

import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/domain/ui_models/device_clip_ui.dart';

part 'device_clips_provider.g.dart';

@riverpod
class DeviceClipsList extends _$DeviceClipsList {
  static const pollInterval = Duration(seconds: 5);

  Timer? _poll;
  int _ticket = 0;
  late String _deviceId;

  @override
  Future<List<DeviceClipUi>> build(String deviceId) async {
    _deviceId = deviceId;
    ref.onDispose(_cancelPoll);
    final clips = await _fetch();
    _schedulePoll(clips);
    return clips;
  }

  Future<void> refresh({bool silent = false}) async {
    final ticket = ++_ticket;
    if (!silent) {
      state = const AsyncLoading();
    }

    try {
      final clips = await _fetch();
      if (!ref.mounted || ticket != _ticket) return;
      state = AsyncData(clips);
      _schedulePoll(clips);
    } catch (error, stackTrace) {
      if (!ref.mounted || ticket != _ticket) return;
      if (silent && state.hasValue) return;
      _cancelPoll();
      state = AsyncError(error, stackTrace);
    }
  }

  Future<List<DeviceClipUi>> _fetch() async {
    final clips = await ref
        .read(devicesRepositoryProvider)
        .listClips(_deviceId);
    return clips.map(DeviceClipUi.fromDto).toList();
  }

  void _schedulePoll(List<DeviceClipUi> clips) {
    if (!clips.any((clip) => clip.isPending)) {
      _cancelPoll();
      return;
    }
    if (_poll != null) return;

    _poll = Timer.periodic(pollInterval, (_) {
      unawaited(refresh(silent: true));
    });
  }

  void _cancelPoll() {
    _poll?.cancel();
    _poll = null;
  }
}
