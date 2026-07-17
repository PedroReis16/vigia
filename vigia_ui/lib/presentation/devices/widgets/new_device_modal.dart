import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';
import 'package:vigia_ui/core/theme/theme_colors.dart';

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
  }

  @override
  void dispose() {
    _videoController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Adicionar dispositivo',
              style: textTheme.titleLarge,
            ),
            const SizedBox(height: 4),
            Text(
              'Siga o tutorial e os passos abaixo para cadastrar um novo Vigia.',
              style: textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            _VideoPreview(controller: _videoController),
            const SizedBox(height: 20),
            Expanded(
              child: ListView.separated(
                itemCount: _steps.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final step = _steps[index];
                  return _StepTile(
                    number: index + 1,
                    title: step.title,
                    description: step.description,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VideoPreview extends StatelessWidget {
  const _VideoPreview({required this.controller});

  final VideoPlayerController controller;

  @override
  Widget build(BuildContext context) {
    if (!controller.value.isInitialized) {
      return const SizedBox(
        height: 180,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: AspectRatio(
        aspectRatio: controller.value.aspectRatio,
        child: VideoPlayer(controller),
      ),
    );
  }
}

class _StepTile extends StatelessWidget {
  const _StepTile({
    required this.number,
    required this.title,
    required this.description,
  });

  final int number;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 28,
          height: 28,
          alignment: Alignment.center,
          decoration: const BoxDecoration(
            color: ThemeColors.accent,
            shape: BoxShape.circle,
          ),
          child: Text(
            '$number',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
              fontSize: 13,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: textTheme.titleMedium),
              const SizedBox(height: 2),
              Text(description, style: textTheme.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}
