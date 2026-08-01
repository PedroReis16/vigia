import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
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

class _DeviceDetailsPageState extends ConsumerState<DeviceDetailsPage> {
  late final VideoPlayerController _controller;
  bool _fullscreen = false;

  @override
  void initState() {
    super.initState();
    _controller = VideoPlayerController.asset('assets/videos/demo.mp4')
      ..setLooping(true)
      ..initialize().then((_) {
        if (!mounted) return;
        setState(() {});
        _controller.play();
      });
  }

  @override
  void dispose() {
    _controller.dispose();
    _restoreSystemUi();
    super.dispose();
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
    if (context.canPop()) context.pop();
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
      return Scaffold(
        backgroundColor: Colors.black,
        body: Stack(
          fit: StackFit.expand,
          children: [
            DeviceVideoPlayer(
              controller: _controller,
              fullscreen: true,
              onToggleFullscreen: _toggleFullscreen,
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
      );
    }

    return Scaffold(
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
          AspectRatio(
            aspectRatio: 16 / 9,
            child: DeviceVideoPlayer(
              controller: _controller,
              fullscreen: false,
              onToggleFullscreen: _toggleFullscreen,
              heroTag: heroTag,
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
