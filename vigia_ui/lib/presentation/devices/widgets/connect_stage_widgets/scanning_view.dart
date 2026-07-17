import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:vigia_ui/presentation/devices/widgets/connect_stage_widgets/step_tile.dart';
import 'package:vigia_ui/presentation/devices/widgets/connect_stage_widgets/video_preview.dart';

class ScanningView extends StatelessWidget {
  const ScanningView({
    required this.videoController,
    required this.steps,
    super.key,
  });

  final VideoPlayerController videoController;
  final List<({String title, String description})> steps;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Adicionar dispositivo', style: textTheme.titleLarge),
        const SizedBox(height: 4),
        Text(
          'Siga o tutorial e aproxime o celular do Vigia. A busca já está em andamento.',
          style: textTheme.bodySmall,
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: VideoPreview(controller: videoController),
        ),
        Expanded(
          child: ListView.separated(
            itemCount: steps.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final step = steps[index];
              return StepTile(
                number: index + 1,
                title: step.title,
                description: step.description,
              );
            },
          ),
        ),
      ],
    );
  }
}
