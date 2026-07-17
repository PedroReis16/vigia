import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/providers/app_bar_config.dart';
import 'package:vigia_ui/presentation/shared/widgets/menu_component.dart';

class BasePage extends ConsumerWidget {
  final StatefulNavigationShell navigationShell;
  const BasePage({super.key, required this.navigationShell});

  void _onMenyTap(int index) {
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
      appBar: AppBar(
        leading: config.showBackButton
            ? IconButton(
                onPressed: () => context.pop(),
                icon: const Icon(Icons.arrow_back_ios_new_rounded),
              )
            : null,
        title: Text(config.title),
        actions: [
          if (config.showFilterButton)
            IconButton(
              tooltip: 'Filtrar fichas',
              onPressed: () => {},
              icon: Badge(
                isLabelVisible: false,
                child: Icon(Icons.filter_alt_outlined),
              ),
            ),
        ],
      ),
      body: navigationShell,
      bottomNavigationBar: MenuComponent(
        currentIndex: navigationShell.currentIndex,
        onItemTap: _onMenyTap,
      ),
    );
  }
}
