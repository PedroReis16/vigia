import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/presentation/home/home_page.dart';
import 'package:vigia_ui/presentation/settings/settings_page.dart';
import 'package:vigia_ui/presentation/shell/animated_shell_body.dart';
import 'package:vigia_ui/presentation/shell/base_page.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _sheetsNavigatorKey = GlobalKey<NavigatorState>();
final _libraryNavigatorKey = GlobalKey<NavigatorState>();

final GoRouter appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: AppRoutes.home,
  debugLogDiagnostics: false,
  routes: [
    StatefulShellRoute(
      builder: (context, state, navigationShell) {
        return BasePage(navigationShell: navigationShell);
      },
      navigatorContainerBuilder: (context, navigationShell, children) {
        return AnimatedShellBody(
          navigationShell: navigationShell,
          children: children,
        );
      },
      branches: [
        // Aba 0 — Home
        StatefulShellBranch(
          navigatorKey: _sheetsNavigatorKey,
          routes: [
            GoRoute(
              path: AppRoutes.home,
              builder: (context, state) => const HomePage(),
              routes: [],
            ),
          ],
        ),
        // Aba 1 — Settings
        StatefulShellBranch(
          navigatorKey: _libraryNavigatorKey,
          routes: [
            GoRoute(
              path: AppRoutes.settings,
              builder: (context, state) => const SettingsPage(),
              routes: [],
            ),
          ],
        ),
      ],
    ),
  ],
);
