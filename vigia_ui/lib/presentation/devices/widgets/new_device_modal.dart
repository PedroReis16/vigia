import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';
import 'package:vigia_ui/core/theme/theme_colors.dart';
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

  static const _padding = EdgeInsets.fromLTRB(16, 0, 16, 24);

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
      ref.read(addDeviceProvider(paired));
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

  Widget _progressIcon() {
    return const SizedBox(
      width: 40,
      height: 40,
      child: CircularProgressIndicator(strokeWidth: 3),
    );
  }

  @override
  Widget build(BuildContext context) {
    final pairing = ref.watch(devicePairingProvider);
    final colors = context.appColors;

    return SafeArea(
      child: Padding(
        padding: _padding,
        child: switch (pairing.stage) {
          DevicePairingStage.scanning => ScanningView(
            videoController: _videoController,
            steps: _steps(context),
          ),
          DevicePairingStage.connecting => StatusView(
            icon: _progressIcon(),
            title: context.translations.connectingTitle,
            description: context.translations.connectingDescription,
          ),
          DevicePairingStage.authenticating => StatusView(
            icon: _progressIcon(),
            title: context.translations.authenticatingTitle,
            description: context.translations.authenticatingDescription,
          ),
          DevicePairingStage.registering => StatusView(
            icon: _progressIcon(),
            title: context.translations.registeringTitle,
            description: context.translations.registeringDescription,
          ),
          DevicePairingStage.fetchingConfig => StatusView(
            icon: _progressIcon(),
            title: context.translations.fetchingConfigTitle,
            description: context.translations.fetchingConfigDescription,
          ),
          DevicePairingStage.provisioning => WifiProvisionForm(
            onSubmit: (ssid, password) {
              return ref
                  .read(devicePairingProvider.notifier)
                  .submitWifi(ssid: ssid, password: password);
            },
          ),
          DevicePairingStage.testingNetwork => StatusView(
            icon: _progressIcon(),
            title: context.translations.testingNetworkTitle,
            description: context.translations.testingNetworkDescription,
          ),
          DevicePairingStage.connected => StatusView(
            icon: Icon(
              Icons.check_circle_rounded,
              color: colors.success,
              size: 56,
            ),
            title: context.translations.connectionEstablished,
            description: context.translations.deviceLinkedSuccess(
              pairing.device?.name ?? context.translations.appTitle,
            ),
            action: SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _onConfirm,
                child: Text(context.translations.confirm),
              ),
            ),
          ),
          DevicePairingStage.error => StatusView(
            icon: Icon(
              Icons.error_outline_rounded,
              color: colors.error,
              size: 56,
            ),
            title: context.translations.connectionFailed,
            description:
                pairing.errorMessage ??
                context.translations.connectionErrorFallback,
            action: SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () =>
                    ref.read(devicePairingProvider.notifier).retry(),
                child: Text(context.translations.tryAgain),
              ),
            ),
          ),
        },
      ),
    );
  }
}
