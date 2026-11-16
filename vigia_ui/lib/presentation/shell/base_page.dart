import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/providers/app_bar_config.dart';
import 'package:vigia_ui/presentation/notifications/providers/notifications_provider.dart';
import 'package:vigia_ui/presentation/notifications/widgets/notifications_inbox_sheet.dart';
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
    final appBarTheme = Theme.of(context).appBarTheme;
    final unreadCount =
        ref.watch(notificationsInboxProvider).asData?.value.unreadCount ?? 0;

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
              actions: [
                IconButton(
                  tooltip: 'Notificações',
                  onPressed: () async {
                    await ref
                        .read(notificationsInboxProvider.notifier)
                        .refresh();
                    if (!context.mounted) return;
                    await showNotificationsInboxSheet(context);
                  },
                  icon: Badge(
                    isLabelVisible: unreadCount > 0,
                    label: Text(unreadCount > 99 ? '99+' : '$unreadCount'),
                    child: const Icon(Icons.notifications_outlined),
                  ),
                ),
              ],
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
