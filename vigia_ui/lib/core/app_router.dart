import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/presentation/devices/pages/device_clips_page.dart';
import 'package:vigia_ui/presentation/devices/pages/device_details_page.dart';
import 'package:vigia_ui/presentation/devices/pages/devices_page.dart';
import 'package:vigia_ui/presentation/settings/pages/settings_page.dart';
import 'package:vigia_ui/presentation/shell/animated_shell_body.dart';
import 'package:vigia_ui/presentation/shell/auth_to_shell_transition.dart';
import 'package:vigia_ui/presentation/shell/auth_to_shell_transition_driver.dart';
import 'package:vigia_ui/presentation/shell/base_page.dart';
import 'package:vigia_ui/presentation/user/pages/auth_page.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';
import 'package:vigia_ui/presentation/user/providers/cold_start_provider.dart';

part 'app_router.g.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _devicesNavigatorKey = GlobalKey<NavigatorState>();
final _settingsNavigatorKey = GlobalKey<NavigatorState>();

@Riverpod(keepAlive: true)
GoRouter appRouter(Ref ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen(authSessionProvider, (_, _) {
    refresh.value++;
  });
  // Only refresh when an enter morph is armed. Listening to disarm() would
  // rebuild the shell page mid-transition (Duration.zero) and flash on device.
  ref.listen(authExitTransitionProvider, (previous, next) {
    if (next == AuthTransitionKind.login ||
        next == AuthTransitionKind.register ||
        next == AuthTransitionKind.coldStart) {
      refresh.value++;
    }
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

      if (loggedIn && onAuth) {
        final kind = ref.read(authExitTransitionProvider);
        // Form login/register arm before session flips. Authenticated cold start
        // arms login only after AuthPage has painted the centered logo.
        if (kind == AuthTransitionKind.login ||
            kind == AuthTransitionKind.register ||
            kind == AuthTransitionKind.coldStart) {
          return AppRoutes.devicesPage;
        }
        // Still on first-boot cold start — keep AuthPage visible.
        if (!ref.read(coldStartCompletedProvider)) {
          return null;
        }
        // Edge case (cold start already completed): leave without morph.
        return AppRoutes.devicesPage;
      }

      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.authPage,
        pageBuilder: (context, state) {
          final kind = ref.read(authExitTransitionProvider);
          final playLogout = kind == AuthTransitionKind.logout;
          if (playLogout) {
            // Extra slack covers precache + hold frame before the morph ticks.
            Future<void>.delayed(
              AuthToShellTransition.duration +
                  const Duration(milliseconds: 120),
              () {
                ref.read(authExitTransitionProvider.notifier).disarm();
              },
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
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              if (!playLogout) return child;
              return AuthToShellTransitionDriver(
                reverse: true,
                // Keep logo on the expanding veil (empty veil → pop-in on device).
                flyLogo: true,
                child: child,
              );
            },
          );
        },
      ),
      StatefulShellRoute(
        pageBuilder: (context, state, navigationShell) {
          final kind = ref.read(authExitTransitionProvider);
          final playLogin =
              kind == AuthTransitionKind.login ||
              kind == AuthTransitionKind.register ||
              kind == AuthTransitionKind.coldStart;
          if (playLogin) {
            // Disarm after morph + warm-up hold — not in a microtask — so a
            // refresh cannot rebuild this page with Duration.zero mid-flight.
            Future<void>.delayed(
              AuthToShellTransition.duration +
                  const Duration(milliseconds: 120),
              () {
                ref.read(authExitTransitionProvider.notifier).disarm();
              },
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
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              if (!playLogin) return child;
              return AuthToShellTransitionDriver(
                // Always fly the logo on the veil — Hero flashes on devices.
                flyLogo: true,
                logoFromCenter: kind == AuthTransitionKind.coldStart,
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
            navigatorKey: _devicesNavigatorKey,
            routes: [
              GoRoute(
                path: AppRoutes.devicesPage,
                builder: (context, state) => const DevicesPage(),
                routes: [
                  GoRoute(
                    path: AppRoutes.deviceDetailsRelative,
                    pageBuilder: (context, state) {
                      final String deviceId = state.pathParameters['deviceId']!;
                      final device = state.extra is DeviceUIModel
                          ? state.extra as DeviceUIModel
                          : null;

                      return CustomTransitionPage(
                        key: state.pageKey,
                        opaque: false,
                        child: DeviceDetailsPage(
                          deviceId: deviceId,
                          device: device,
                        ),
                        transitionDuration: const Duration(milliseconds: 340),
                        reverseTransitionDuration: const Duration(
                          milliseconds: 300,
                        ),
                        transitionsBuilder:
                            (context, animation, secondaryAnimation, child) {
                              final fade = CurvedAnimation(
                                parent: animation,
                                curve: Curves.easeOutCubic,
                                reverseCurve: Curves.easeInCubic,
                              );

                              return FadeTransition(
                                opacity: fade,
                                child: child,
                              );
                            },
                      );
                    },
                    routes: [
                      GoRoute(
                        path: AppRoutes.deviceClipsRelative,
                        builder: (context, state) => DeviceClipsPage(
                          deviceId: state.pathParameters['deviceId']!,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _settingsNavigatorKey,
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
