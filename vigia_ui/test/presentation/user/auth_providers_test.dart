import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/core/providers/token_storage_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/pending_invite_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';
import 'package:vigia_ui/presentation/user/providers/cold_start_provider.dart';

import '../../helpers/fake_token_storage.dart';

void main() {
  group('AuthSession', () {
    test('build is false when refresh token is missing', () async {
      final storage = FakeTokenStorage();
      final container = ProviderContainer(
        overrides: [tokenStorageProvider.overrideWithValue(storage)],
      );
      addTearDown(container.dispose);

      await expectLater(
        container.read(authSessionProvider.future),
        completion(isFalse),
      );
      expect(container.read(authSessionProvider).asData?.value, isFalse);
    });

    test('build is true when refresh token is present', () async {
      final storage = FakeTokenStorage(refreshToken: 'refresh');
      final container = ProviderContainer(
        overrides: [tokenStorageProvider.overrideWithValue(storage)],
      );
      addTearDown(container.dispose);

      await expectLater(
        container.read(authSessionProvider.future),
        completion(isTrue),
      );
    });

    test('setAuthenticated persists tokens and marks session true', () async {
      final storage = FakeTokenStorage();
      final container = ProviderContainer(
        overrides: [tokenStorageProvider.overrideWithValue(storage)],
      );
      addTearDown(container.dispose);

      await container.read(authSessionProvider.future);
      await container
          .read(authSessionProvider.notifier)
          .setAuthenticated(accessToken: 'access', refreshToken: 'refresh');

      expect(storage.accessToken, 'access');
      expect(storage.refreshToken, 'refresh');
      expect(container.read(authSessionProvider).asData?.value, isTrue);
    });

    test('clearSession clears tokens and marks session false', () async {
      final storage = FakeTokenStorage(
        accessToken: 'access',
        refreshToken: 'refresh',
      );
      final container = ProviderContainer(
        overrides: [tokenStorageProvider.overrideWithValue(storage)],
      );
      addTearDown(container.dispose);

      await container.read(authSessionProvider.future);
      await container.read(authSessionProvider.notifier).clearSession();

      expect(storage.accessToken, isNull);
      expect(storage.refreshToken, isNull);
      expect(container.read(authSessionProvider).asData?.value, isFalse);
    });
  });

  group('ColdStartCompleted', () {
    test('starts false and complete flips to true', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      expect(container.read(coldStartCompletedProvider), isFalse);
      container.read(coldStartCompletedProvider.notifier).complete();
      expect(container.read(coldStartCompletedProvider), isTrue);
    });
  });

  group('PendingInviteToken', () {
    test('setToken and clear update state', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      expect(container.read(pendingInviteTokenProvider), isNull);

      container.read(pendingInviteTokenProvider.notifier).setToken('invite-1');
      expect(container.read(pendingInviteTokenProvider), 'invite-1');

      container.read(pendingInviteTokenProvider.notifier).clear();
      expect(container.read(pendingInviteTokenProvider), isNull);
    });
  });

  group('AuthExitTransition', () {
    test('arm helpers set kind and disarm resets', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(authExitTransitionProvider.notifier);

      expect(
        container.read(authExitTransitionProvider),
        AuthTransitionKind.none,
      );

      notifier.armLogin();
      expect(
        container.read(authExitTransitionProvider),
        AuthTransitionKind.login,
      );

      notifier.armRegister();
      expect(
        container.read(authExitTransitionProvider),
        AuthTransitionKind.register,
      );

      notifier.armColdStart();
      expect(
        container.read(authExitTransitionProvider),
        AuthTransitionKind.coldStart,
      );

      notifier.armLogout();
      expect(
        container.read(authExitTransitionProvider),
        AuthTransitionKind.logout,
      );

      notifier.disarm();
      expect(
        container.read(authExitTransitionProvider),
        AuthTransitionKind.none,
      );
    });
  });
}
