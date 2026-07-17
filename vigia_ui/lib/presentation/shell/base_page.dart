import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/providers/app_bar_config.dart';
import 'package:vigia_ui/presentation/shared/widgets/menu_component.dart';

class BasePage extends ConsumerWidget {
  final StatefulNavigationShell navigationShell;
  const BasePage({super.key, required this.navigationShell});

  void _onMenuTap(int index) {
    navigationShell.goBranch(
      index,
      initialLocation: index == navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = AppBarConfig.fromState(GoRouterState.of(context));
    // final hasActiveFilters = ref.watch(sheetsFilterProvider).hasActiveFilters;
 
    
    return Scaffold(
      appBar: !config.showAppBar
          ? null
          : AppBar(
              title: Text(config.title),
            ),
      body: navigationShell,
      bottomNavigationBar: !config.showAppBar
          ? null
          : MenuComponent(
              currentIndex: navigationShell.currentIndex,
              onItemTap: _onMenuTap,
            ),
    );
  }
}
