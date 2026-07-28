import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/presentation/devices/pages/device_live_page.dart';
import 'package:vigia_ui/presentation/devices/pages/devices_page.dart';
import 'package:vigia_ui/presentation/settings/pages/settings_page.dart';
import 'package:vigia_ui/presentation/shell/animated_shell_body.dart';
import 'package:vigia_ui/presentation/shell/base_page.dart';
import 'package:vigia_ui/presentation/user/pages/login_page.dart';
import 'package:vigia_ui/presentation/user/pages/register_page.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _sheetsNavigatorKey = GlobalKey<NavigatorState>();
final _libraryNavigatorKey = GlobalKey<NavigatorState>();

final GoRouter appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: AppRoutes.loginPage,
  debugLogDiagnostics: false,
  routes: [
    GoRoute(
      path: AppRoutes.loginPage,
      pageBuilder: (context, state) => CustomTransitionPage(
        key: state.pageKey,
        child: const LoginPage(),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          // fade, slide, etc.
          return FadeTransition(opacity: animation, child: child);
        },
      ),
    ),
    GoRoute(
      path: AppRoutes.registerPage,
      pageBuilder: (context, state) => CustomTransitionPage(
        key: state.pageKey,
        child: const RegisterPage(),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(opacity: animation, child: child);
        },
      ),
    ),
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
              path: AppRoutes.devicesPage,
              builder: (context, state) => const DevicesPage(),
              routes: [
                GoRoute(
                  path: AppRoutes.deviceStreamRelative,
                  pageBuilder: (context, state) {
                    final String deviceId = state.pathParameters['deviceId']!;

                    return CustomTransitionPage(
                      key: state.pageKey,
                      child: DeviceLivePage(deviceId: deviceId),
                      transitionsBuilder:
                          (context, animation, secondaryAnimation, child) {
                            // Define o início (fora da tela à direita) e o fim (centro)
                            const begin = Offset(1.0, 0.0);
                            const end = Offset.zero;
                            const curve = Curves.ease;

                            final tween = Tween(
                              begin: begin,
                              end: end,
                            ).chain(CurveTween(curve: curve));

                            return SlideTransition(
                              position: animation.drive(tween),
                              child: child,
                            );
                          },
                    );
                  },
                ),
              ],
            ),
          ],
        ),
        // Aba 1 — Settings
        StatefulShellBranch(
          navigatorKey: _libraryNavigatorKey,
          routes: [
            GoRoute(
              path: AppRoutes.settingsPage,
              builder: (context, state) => const SettingsPage(),
              routes: [],
            ),
          ],
        ),
      ],
    ),
  ],
);
