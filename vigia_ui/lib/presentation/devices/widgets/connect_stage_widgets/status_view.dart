import 'package:flutter/material.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

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
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    final colorScheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(context.translations.addDevice, style: textTheme.titleLarge),
        const Spacer(),
        Center(
          child: Container(
            width: 88,
            height: 88,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: colorScheme.primaryContainer,
              shape: BoxShape.circle,
            ),
            child: icon,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          title,
          style: textTheme.titleMedium,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          description,
          style: textTheme.bodyMedium?.copyWith(
            color: colorScheme.onSurfaceVariant,
          ),
          textAlign: TextAlign.center,
        ),
        const Spacer(),
        ?action,
      ],
    );
  }
}
