import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';

class DeviceLivePage extends ConsumerStatefulWidget {
  const DeviceLivePage({super.key, required this.deviceId});
  final String deviceId;

  @override
  ConsumerState<DeviceLivePage> createState() => _DeviceLivePageState();
}

class _DeviceLivePageState extends ConsumerState<DeviceLivePage> {
  late final String _deviceId;
  late final VideoPlayerController _controller;

  @override
  void initState() {
    super.initState();
    _deviceId = widget.deviceId;

    _controller = VideoPlayerController.asset('assets/videos/demo.mp4')
      ..setLooping(true)
      ..initialize().then((_) {
        if (!mounted) return;
        setState(() {});
        _controller.play();
      });

    // Força a página de streaming em modo paisagem.
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    // Opcional: modo imersivo (esconde barras do sistema) para streaming.
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  }

  @override
  void dispose() {
    _controller.dispose();

    // Restaura a orientação e a UI do sistema ao sair da página.
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
    ]);
    SystemChrome.setEnabledSystemUIMode(
      SystemUiMode.manual,
      overlays: SystemUiOverlay.values,
    );
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          if (_controller.value.isInitialized)
            Positioned.fill(
              child: FittedBox(
                fit: BoxFit.cover,
                child: SizedBox(
                  width: _controller.value.size.width,
                  height: _controller.value.size.height,
                  child: VideoPlayer(_controller),
                ),
              ),
            ),
          Positioned(
            top: 20,
            left: 20,
            child: IconButton(
              onPressed: () => context.pop(),
              icon: const Icon(Icons.arrow_back_ios_new_rounded),
            ),
          ),
        ],
      ),
    );
  }
}
