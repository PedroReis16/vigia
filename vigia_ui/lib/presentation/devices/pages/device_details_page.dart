import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/data/services/whep_live_session.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/device_live_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_details.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_video_player.dart';

class DeviceDetailsPage extends ConsumerStatefulWidget {
  const DeviceDetailsPage({super.key, required this.deviceId, this.device});

  final String deviceId;
  final DeviceUIModel? device;

  @override
  ConsumerState<DeviceDetailsPage> createState() => _DeviceDetailsPageState();
}

class _DeviceDetailsPageState extends ConsumerState<DeviceDetailsPage>
    with WidgetsBindingObserver {
  late final WhepLiveSession _session;
  bool _fullscreen = false;
  bool _starting = false;
  bool _leaving = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _session = WhepLiveSession(whepUrl: deviceWhepUrl(widget.deviceId));
    _session.addListener(_onSessionUpdate);
    WidgetsBinding.instance.addPostFrameCallback((_) => _startLive());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _session.removeListener(_onSessionUpdate);
    // Safety net for non-PopScope exits — prefer [_leave] so teardown finishes
    // before the route (and Hero) tear down the RTCVideoView.
    unawaited(_session.close());
    unawaited(_restoreSystemUi());
    super.dispose();
  }

  void _onSessionUpdate() {
    if (mounted) setState(() {});
  }

  @override
  void didChangeMetrics() {
    // Rebuild when the soft keyboard opens/closes so the video can collapse.
    if (mounted) setState(() {});
  }

  Future<void> _startLive() async {
    if (_starting || !mounted) return;
    _starting = true;
    _session.beginConnecting();

    try {
      await _session.initialize();
      if (!mounted) return;

      ref.invalidate(startDeviceStreamingProvider(widget.deviceId));
      await ref.read(startDeviceStreamingProvider(widget.deviceId).future);
      if (!mounted) return;

      await _session.connect();
    } catch (e) {
      if (!mounted) return;
      _session.markError(e);
    } finally {
      _starting = false;
    }
  }

  Future<void> _retryLive() async {
    if (_starting) return;
    await _startLive();
  }

  DeviceUIModel? _resolveDevice(List<DeviceUIModel>? devices) {
    if (devices != null) {
      for (final device in devices) {
        if (device.id == widget.deviceId) return device;
      }
    }
    return widget.device;
  }

  /// Switch layout first, then rotate — avoids portrait Column overflowing
  /// while the window is already landscape.
  Future<void> _enterFullscreen() async {
    if (!mounted) return;
    setState(() => _fullscreen = true);
    await SystemChrome.setPreferredOrientations([
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    await SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  }

  /// Rotate back first while still on the immersive layout, then restore chrome.
  Future<void> _exitFullscreen() async {
    await _restoreSystemUi();
    if (!mounted) return;
    setState(() => _fullscreen = false);
  }

  Future<void> _restoreSystemUi() async {
    await SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
    ]);
    await SystemChrome.setEnabledSystemUIMode(
      SystemUiMode.manual,
      overlays: SystemUiOverlay.values,
    );
  }

  Future<void> _toggleFullscreen() async {
    if (_fullscreen) {
      await _exitFullscreen();
    } else {
      await _enterFullscreen();
    }
  }

  Future<void> _onBack() async {
    if (_fullscreen) {
      await _exitFullscreen();
      return;
    }
    await _leave();
  }

  /// Tear down WebRTC before the route pop so Hero / dispose never race the
  /// native video texture (that race freezes the whole app).
  Future<void> _leave() async {
    if (_leaving) return;
    _leaving = true;
    try {
      try {
        await _session.close();
      } catch (_) {
        // Still leave the page even if peer teardown fails.
      }
      await _restoreSystemUi();
      if (!mounted) return;
      if (context.canPop()) context.pop();
    } finally {
      if (mounted) _leaving = false;
    }
  }

  Future<void> _onPopInvoked(bool didPop, Object? result) async {
    if (didPop) return;
    if (_fullscreen) {
      await _exitFullscreen();
      return;
    }
    await _leave();
  }

  @override
  Widget build(BuildContext context) {
    final devices = ref.watch(devicesProvider).asData?.value;
    final device = _resolveDevice(devices);
    final nickname = device?.nickname ?? context.translations.devices;
    final heroTag = 'device-thumb-${widget.deviceId}';
    final isLandscape =
        MediaQuery.orientationOf(context) == Orientation.landscape;
    final showFullscreen = _fullscreen || isLandscape;

    if (showFullscreen) {
      return PopScope(
        canPop: false,
        onPopInvokedWithResult: _onPopInvoked,
        child: Scaffold(
          backgroundColor: Colors.black,
          body: Stack(
            fit: StackFit.expand,
            children: [
              DeviceVideoPlayer(
                session: _session,
                fullscreen: true,
                onToggleFullscreen: _toggleFullscreen,
                onRetry: _retryLive,
              ),
              SafeArea(
                child: Align(
                  alignment: Alignment.topLeft,
                  child: IconButton(
                    onPressed: _onBack,
                    color: Colors.white,
                    icon: const Icon(Icons.arrow_back_ios_new_rounded),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // BasePage's Scaffold already consumes MediaQuery.viewInsets, so reading
    // viewInsetsOf here is always 0. Use the platform view inset instead, and
    // depend on size so we still rebuild when the keyboard opens/closes.
    MediaQuery.sizeOf(context);
    final keyboardVisible = View.of(context).viewInsets.bottom > 0;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: _onPopInvoked,
      child: Scaffold(
        resizeToAvoidBottomInset: false,
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(kToolbarHeight),
          child: _RouteReveal(
            begin: 0.2,
            child: AppBar(
              title: Text(nickname),
              leading: IconButton(
                onPressed: _onBack,
                icon: const Icon(Icons.arrow_back_ios_new_rounded),
              ),
            ),
          ),
        ),
        body: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ClipRect(
              child: AnimatedAlign(
                duration: const Duration(milliseconds: 220),
                curve: Curves.easeOutCubic,
                alignment: Alignment.topCenter,
                heightFactor: keyboardVisible ? 0 : 1,
                child: AspectRatio(
                  aspectRatio: 16 / 9,
                  child: DeviceVideoPlayer(
                    session: _session,
                    fullscreen: false,
                    onToggleFullscreen: _toggleFullscreen,
                    onRetry: _retryLive,
                    heroTag: heroTag,
                  ),
                ),
              ),
            ),
            Expanded(
              child: _RouteReveal(
                begin: 0.18,
                slide: const Offset(0, 0.02),
                child: device == null
                    ? Center(child: Text(context.translations.noDevicesFound))
                    : DeviceDetails(device: device),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Fades (and optionally slides) in with the enclosing route animation so the
/// Hero media leads and the rest of the page settles in quietly.
class _RouteReveal extends StatelessWidget {
  const _RouteReveal({required this.child, this.begin = 0.2, this.slide});

  final Widget child;
  final double begin;
  final Offset? slide;

  @override
  Widget build(BuildContext context) {
    final animation = ModalRoute.of(context)?.animation;
    if (animation == null) return child;

    final reveal = CurvedAnimation(
      parent: animation,
      curve: Interval(begin, 1.0, curve: Curves.easeOutCubic),
      reverseCurve: Curves.easeInCubic,
    );

    Widget result = FadeTransition(opacity: reveal, child: child);
    if (slide != null) {
      result = SlideTransition(
        position: Tween<Offset>(begin: slide, end: Offset.zero).animate(reveal),
        child: result,
      );
    }
    return result;
  }
}
