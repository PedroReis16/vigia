import 'package:flutter/material.dart';

class MenuComponent extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onItemTap;

  const MenuComponent({
    super.key,
    required this.currentIndex,
    required this.onItemTap,
  });

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          IconButton(
            onPressed: () => onItemTap(0),
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
