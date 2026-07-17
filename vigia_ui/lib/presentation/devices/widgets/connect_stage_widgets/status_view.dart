import 'package:flutter/material.dart';

class StatusView extends StatelessWidget {
  const StatusView({
    required this.icon,
    required this.title,
    required this.description,
    this.action,
    super.key,
  });

  final Widget icon;
  final String title;
  final String description;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Adicionar dispositivo', style: textTheme.titleLarge),
        const Spacer(),
        Center(child: icon),
        const SizedBox(height: 20),
        Text(
          title,
          style: textTheme.titleLarge,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          description,
          style: textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),
        const Spacer(),
        ?action,
      ],
    );
  }
}
