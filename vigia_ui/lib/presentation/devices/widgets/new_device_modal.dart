import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';
import 'package:vigia_ui/domain/enums/device_pairing_stage.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/device_pairing_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/devices/widgets/connect_stage_widgets/scanning_view.dart';
import 'package:vigia_ui/presentation/devices/widgets/connect_stage_widgets/status_view.dart';
import 'package:vigia_ui/presentation/devices/widgets/connect_stage_widgets/wifi_provision_form.dart';

class NewDeviceModal extends ConsumerStatefulWidget {
  const NewDeviceModal({super.key});

  @override
  ConsumerState<NewDeviceModal> createState() => _NewDeviceModalState();
}

class _NewDeviceModalState extends ConsumerState<NewDeviceModal> {
  late final VideoPlayerController _videoController;

  @override
  void initState() {
    super.initState();
    _videoController = VideoPlayerController.asset(
      'assets/videos/connect_tutorial.mp4',
    );
    _videoController
      ..setLooping(true)
      ..setVolume(0)
      ..initialize().then((_) {
        if (!mounted) return;
        setState(() {});
        _videoController.play();
      });

    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(devicePairingProvider.notifier).start();
    });
  }

  @override
  void dispose() {
    _videoController.dispose();
    super.dispose();
  }

  Future<void> _onConfirm() async {
    final paired = ref.read(devicePairingProvider).device;
    if (paired != null) {
      ref.read(devicesProvider.notifier).addDevice(paired);
    }
    if (!mounted) return;
    Navigator.of(context).pop();
  }

  List<({String title, String description})> _steps(BuildContext context) {
    return [
      (
        title: context.translations.stepPowerOnTitle,
        description: context.translations.stepPowerOnDescription,
      ),
      (
        title: context.translations.stepPairTitle,
        description: context.translations.stepPairDescription,
      ),
      (
        title: context.translations.stepWaitTitle,
        description: context.translations.stepWaitDescription,
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final pairing = ref.watch(devicePairingProvider);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: switch (pairing.stage) {
          DevicePairingStage.scanning => ScanningView(
            videoController: _videoController,
            steps: _steps(context),
          ),
          DevicePairingStage.connecting => StatusView(
            icon: const CircularProgressIndicator(),
            title: context.translations.connectingTitle,
            description: context.translations.connectingDescription,
          ),
          DevicePairingStage.authenticating => StatusView(
            icon: const CircularProgressIndicator(),
            title: context.translations.authenticatingTitle,
            description: context.translations.authenticatingDescription,
          ),
          DevicePairingStage.provisioning => WifiProvisionForm(
            onSubmit: (ssid, password) {
              return ref
                  .read(devicePairingProvider.notifier)
                  .submitWifi(ssid: ssid, password: password);
            },
          ),
          DevicePairingStage.connected => StatusView(
            icon: Icon(
              Icons.check_circle_rounded,
              color: Theme.of(context).colorScheme.primary,
              size: 56,
            ),
            title: context.translations.connectionEstablished,
            description: context.translations.deviceLinkedSuccess(
              pairing.device?.nickname ?? context.translations.appTitle,
            ),
            action: FilledButton(
              onPressed: _onConfirm,
              child: Text(context.translations.confirm),
            ),
          ),
          DevicePairingStage.error => StatusView(
            icon: Icon(
              Icons.error_outline_rounded,
              color: Colors.red.shade400,
              size: 56,
            ),
            title: context.translations.connectionFailed,
            description:
                pairing.errorMessage ??
                context.translations.connectionErrorFallback,
            action: OutlinedButton(
              onPressed: () => ref.read(devicePairingProvider.notifier).retry(),
              child: Text(context.translations.tryAgain),
            ),
          ),
        },
      ),
    );
  }
}
