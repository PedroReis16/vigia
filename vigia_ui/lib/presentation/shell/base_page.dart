import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/providers/app_bar_config.dart';
import 'package:vigia_ui/presentation/shared/widgets/menu_component.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';

class BasePage extends StatelessWidget {
  final StatefulNavigationShell navigationShell;
  const BasePage({super.key, required this.navigationShell});

  void _onMenuTap(int index) {
    navigationShell.goBranch(
      index,
      initialLocation: index == navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context) {
    final config = AppBarConfig.fromState(context, GoRouterState.of(context));
    final appBarTheme = Theme.of(context).appBarTheme;
    // Logo flight is drawn on the enter morph veil — no AppBar Hero
    // (Hero placeholders flash shell content on physical devices).

    return Scaffold(
      appBar: !config.showAppBar
          ? null
          : AppBar(
              backgroundColor: appBarTheme.backgroundColor,
              foregroundColor: appBarTheme.foregroundColor,
              systemOverlayStyle: SystemUiOverlayStyle.light,
              centerTitle: true,
              title: Material(
                type: MaterialType.transparency,
                child: VigiaLogoHero.image(height: VigiaLogoHero.appBarHeight),
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
