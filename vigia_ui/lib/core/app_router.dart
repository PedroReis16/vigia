import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/presentation/devices/pages/device_live_page.dart';
import 'package:vigia_ui/presentation/devices/pages/devices_page.dart';
import 'package:vigia_ui/presentation/settings/pages/settings_page.dart';
import 'package:vigia_ui/presentation/shell/animated_shell_body.dart';
import 'package:vigia_ui/presentation/shell/base_page.dart';
import 'package:vigia_ui/presentation/user/pages/auth_page.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'app_router.g.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _sheetsNavigatorKey = GlobalKey<NavigatorState>();
final _libraryNavigatorKey = GlobalKey<NavigatorState>();

@Riverpod(keepAlive: true)
GoRouter appRouter(Ref ref) {
  // Notifies GoRouter to re-run [redirect] when auth changes, without
  // recreating the router instance.
  final refresh = ValueNotifier<int>(0);
  ref.listen(authSessionProvider, (_, _) {
    refresh.value++;
  });
  ref.onDispose(refresh.dispose);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: AppRoutes.authPage,
    refreshListenable: refresh,
    debugLogDiagnostics: false,
    redirect: (context, state) {
      final auth = ref.read(authSessionProvider);

      // Wait until we know whether a session exists.
      if (auth.isLoading) return null;

      final loggedIn = auth.asData?.value ?? false;
      final onAuth = state.matchedLocation == AppRoutes.authPage;

      if (!loggedIn && !onAuth) return AppRoutes.authPage;
      if (loggedIn && onAuth) return AppRoutes.devicesPage;
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.authPage,
        builder: (context, state) => const AuthPage(),
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
}
