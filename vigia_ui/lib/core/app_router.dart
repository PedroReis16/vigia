import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/presentation/devices/pages/device_live_page.dart';
import 'package:vigia_ui/presentation/devices/pages/devices_page.dart';
import 'package:vigia_ui/presentation/settings/pages/settings_page.dart';
import 'package:vigia_ui/presentation/shell/animated_shell_body.dart';
import 'package:vigia_ui/presentation/shell/auth_to_shell_transition.dart';
import 'package:vigia_ui/presentation/shell/base_page.dart';
import 'package:vigia_ui/presentation/user/pages/auth_page.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'app_router.g.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _sheetsNavigatorKey = GlobalKey<NavigatorState>();
final _libraryNavigatorKey = GlobalKey<NavigatorState>();

@Riverpod(keepAlive: true)
GoRouter appRouter(Ref ref) {
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
        pageBuilder: (context, state) {
          final kind = ref.read(authExitTransitionProvider);
          final playLogout = kind == AuthTransitionKind.logout;
          if (playLogout) {
            Future.microtask(
              () => ref.read(authExitTransitionProvider.notifier).disarm(),
            );
          }

          return CustomTransitionPage(
            key: state.pageKey,
            child: const AuthPage(),
            transitionDuration: playLogout
                ? AuthToShellTransition.duration
                : Duration.zero,
            reverseTransitionDuration: Duration.zero,
            opaque: !playLogout,
            transitionsBuilder:
                (context, animation, secondaryAnimation, child) {
                  if (!playLogout) return child;
                  return AuthToShellTransition(
                    animation: animation,
                    reverse: true,
                    child: child,
                  );
                },
          );
        },
      ),
      StatefulShellRoute(
        pageBuilder: (context, state, navigationShell) {
          final kind = ref.read(authExitTransitionProvider);
          final playLogin = kind == AuthTransitionKind.login || kind == AuthTransitionKind.register;
          if (playLogin) {
            Future.microtask(
              () => ref.read(authExitTransitionProvider.notifier).disarm(),
            );
          }

          return CustomTransitionPage(
            key: state.pageKey,
            child: BasePage(navigationShell: navigationShell),
            transitionDuration: playLogin
                ? AuthToShellTransition.duration
                : Duration.zero,
            reverseTransitionDuration: Duration.zero,
            opaque: !playLogin,
            transitionsBuilder:
                (context, animation, secondaryAnimation, child) {
                  if (!playLogin) return child;
                  return AuthToShellTransition(
                    animation: animation,
                    child: child,
                  );
                },
          );
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
