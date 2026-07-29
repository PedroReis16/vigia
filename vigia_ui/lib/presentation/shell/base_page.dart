import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/providers/app_bar_config.dart';
import 'package:vigia_ui/presentation/shared/widgets/menu_component.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';

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
    final config = AppBarConfig.fromState(context, GoRouterState.of(context));
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: !config.showAppBar
          ? null
          : AppBar(
              backgroundColor: colorScheme.primary,
              foregroundColor: colorScheme.onPrimary,
              systemOverlayStyle: SystemUiOverlayStyle.light,
              centerTitle: true,
              // Title text temporarily replaced by the centered logo.
              title: Hero(
                tag: VigiaLogoHero.tag,
                // Avoid a second logo flash while the flight is in progress.
                placeholderBuilder: (context, size, child) =>
                    SizedBox(width: size.width, height: size.height),
                child: Material(
                  type: MaterialType.transparency,
                  child: VigiaLogoHero.image(
                    height: VigiaLogoHero.appBarHeight,
                  ),
                ),
              ),
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
