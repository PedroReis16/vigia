import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/core/app_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/core/providers/token_storage_provider.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/presentation/devices/providers/device_details_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/pending_invite_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';
import 'package:vigia_ui/presentation/user/providers/cold_start_provider.dart';

import '../helpers/fake_token_storage.dart';
import '../helpers/pump_app.dart';

class _LoggedOutSession extends AuthSession {
  @override
  Future<bool> build() async => false;
}

class _LoggedInSession extends AuthSession {
  @override
  Future<bool> build() async => true;
}

class _ColdStartDone extends ColdStartCompleted {
  @override
  bool build() => true;
}

class _EmptyDevices extends Devices {
  @override
  Future<List<DeviceUIModel>> build() async => const [];
}

class _HangingShareActions extends DeviceShareActions {
  @override
  AsyncValue<void> build() => const AsyncData(null);

  @override
  Future<void> acceptInvite(String token) => Completer<void>().future;
}

class _SeededPendingInvite extends PendingInviteToken {
  _SeededPendingInvite(this._token);

  final String _token;

  @override
  String? build() => _token;
}

class _ArmedLogin extends AuthExitTransition {
  @override
  AuthTransitionKind build() => AuthTransitionKind.login;
}

ProviderContainer _container({
  required bool loggedIn,
  bool coldStartDone = true,
  String? pendingInvite,
  List<Override> extra = const [],
}) {
  return ProviderContainer(
    overrides: [
      tokenStorageProvider.overrideWithValue(FakeTokenStorage()),
      authSessionProvider.overrideWith(
        loggedIn ? _LoggedInSession.new : _LoggedOutSession.new,
      ),
      coldStartCompletedProvider.overrideWith(
        coldStartDone ? _ColdStartDone.new : ColdStartCompleted.new,
      ),
      devicesProvider.overrideWith(_EmptyDevices.new),
      deviceShareActionsProvider.overrideWith(_HangingShareActions.new),
      if (pendingInvite != null)
        pendingInviteTokenProvider.overrideWith(
          () => _SeededPendingInvite(pendingInvite),
        ),
      ...extra,
    ],
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('appRouter redirects', () {
    testWidgets('unauthenticated navigation to devices redirects to auth', (
      tester,
    ) async {
      final container = _container(loggedIn: false);
      addTearDown(container.dispose);

      final router = container.read(appRouterProvider);
      await pumpRouterApp(tester, container: container, router: router);
      await tester.pumpAndSettle();

      router.go(AppRoutes.devicesPage);
      await tester.pumpAndSettle();

      expect(router.state.matchedLocation, AppRoutes.authPage);
    });

    testWidgets(
      'authenticated on auth with cold start done leaves to devices',
      (tester) async {
        final container = _container(loggedIn: true, coldStartDone: true);
        addTearDown(container.dispose);

        final router = container.read(appRouterProvider);
        await pumpRouterApp(tester, container: container, router: router);
        await tester.pumpAndSettle();

        expect(router.state.matchedLocation, AppRoutes.devicesPage);
      },
    );

    testWidgets(
      'authenticated on auth with pending invite redirects to invite',
      (tester) async {
        final container = _container(
          loggedIn: true,
          coldStartDone: true,
          pendingInvite: 'invite-token',
        );
        addTearDown(container.dispose);

        final router = container.read(appRouterProvider);
        await pumpRouterApp(tester, container: container, router: router);
        await tester.pump();

        expect(
          router.state.matchedLocation,
          AppRoutes.invitePagePath('invite-token'),
        );
      },
    );

    testWidgets(
      'unauthenticated invite path stores token and redirects to auth',
      (tester) async {
        final container = _container(loggedIn: false);
        addTearDown(container.dispose);

        final router = container.read(appRouterProvider);
        await pumpRouterApp(tester, container: container, router: router);
        await tester.pumpAndSettle();

        router.go(AppRoutes.invitePagePath('deep-link-token'));
        await tester.pumpAndSettle();

        expect(router.state.matchedLocation, AppRoutes.authPage);
        expect(container.read(pendingInviteTokenProvider), 'deep-link-token');
      },
    );

    testWidgets('authenticated leaving auth with login armed goes to devices', (
      tester,
    ) async {
      final container = _container(
        loggedIn: true,
        coldStartDone: true,
        extra: [authExitTransitionProvider.overrideWith(_ArmedLogin.new)],
      );
      addTearDown(container.dispose);

      final router = container.read(appRouterProvider);
      await pumpRouterApp(tester, container: container, router: router);

      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));

      expect(router.state.matchedLocation, AppRoutes.devicesPage);

      // Flush GoRouter morph disarm timer (duration + 120ms).
      await tester.pump(const Duration(milliseconds: 1000));
    });
  });
}
