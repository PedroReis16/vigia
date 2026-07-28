import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';
import 'package:vigia_ui/domain/enums/device_pairing_stage.dart';
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
  static const _steps = [
    (
      title: 'Ligue o dispositivo',
      description:
          'Conecte o Vigia à tomada e aguarde até que a luz indique que ele está pronto para a configuração.',
    ),
    (
      title: 'Vincule ao aplicativo',
      description:
          'Aproxime o celular do Vigia para iniciar o vínculo com o aplicativo.',
    ),
    (
      title: 'Aguarde a confirmação',
      description:
          'Aguarde alguns segundos até que a configuração seja concluída com sucesso.',
    ),
  ];

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

  @override
  Widget build(BuildContext context) {
    final pairing = ref.watch(devicePairingProvider);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: switch (pairing.stage) {
          DevicePairingStage.scanning => ScanningView(
            videoController: _videoController,
            steps: _steps,
          ),
          DevicePairingStage.connecting => const StatusView(
            icon: CircularProgressIndicator(),
            title: 'Conectando',
            description:
                'Dispositivo encontrado. Estabelecendo a conexão com o Vigia…',
          ),
          DevicePairingStage.authenticating => const StatusView(
            icon: CircularProgressIndicator(),
            title: 'Validando dispositivo',
            description:
                'Confirmando a identidade do Vigia e autenticando o aplicativo…',
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
            title: 'Conexão estabelecida',
            description:
                '${pairing.device?.description ?? 'Vigia'} foi vinculado com sucesso.',
            action: FilledButton(
              onPressed: _onConfirm,
              child: const Text('Confirmar'),
            ),
          ),
          DevicePairingStage.error => StatusView(
            icon: Icon(
              Icons.error_outline_rounded,
              color: Colors.red.shade400,
              size: 56,
            ),
            title: 'Não foi possível conectar',
            description:
                pairing.errorMessage ??
                'Ocorreu um erro ao procurar ou conectar ao dispositivo.',
            action: OutlinedButton(
              onPressed: () =>
                  ref.read(devicePairingProvider.notifier).retry(),
              child: const Text('Tentar novamente'),
            ),
          ),
        },
      ),
    );
  }
}
