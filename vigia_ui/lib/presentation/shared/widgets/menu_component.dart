import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';

class MenuComponent extends ConsumerWidget {
  final int currentIndex;
  final ValueChanged<int> onItemTap;

  const MenuComponent({
    super.key,
    required this.currentIndex,
    required this.onItemTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          IconButton(
            onPressed: () {
              if (!ref.watch(devicesProvider).isLoading && currentIndex == 0) {
                ref.read(devicesProvider.notifier).refresh();
                return;
              }

              onItemTap(0);
            },
            icon: Icon(
              Icons.dashboard_rounded,
              color: currentIndex == 0
                  ? colorScheme.primary
                  : colorScheme.onSurface.withValues(alpha: 0.4),
            ),
          ),
          IconButton(
            onPressed: () => onItemTap(1),
            icon: Icon(
              Icons.settings,
              color: currentIndex == 1
                  ? colorScheme.primary
                  : colorScheme.onSurface.withValues(alpha: 0.4),
            ),
          ),
        ],
      ),
    );
  }
}
