import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';
import 'package:vigia_ui/presentation/devices/pages/accept_invite_page.dart';
import 'package:vigia_ui/presentation/devices/providers/device_details_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/pending_invite_provider.dart';

import '../helpers/pump_app.dart';

class _ExpiredShare extends DeviceShareActions {
  @override
  AsyncValue<void> build() => const AsyncData(null);

  @override
  Future<void> acceptInvite(String token) async {
    throw RequestException(
      message: 'expired',
      errorCode: ErrorCodes.inviteExpired,
    );
  }
}

void main() {
  testWidgets('failed accept keeps the pending token', (tester) async {
    pendingInviteStoreOverride = MemoryPendingInviteStore();
    addTearDown(() => pendingInviteStoreOverride = null);

    final container = ProviderContainer(
      overrides: [
        deviceShareActionsProvider.overrideWith(_ExpiredShare.new),
      ],
    );
    addTearDown(container.dispose);
    container.read(pendingInviteTokenProvider.notifier).setToken('tok');

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          locale: testLocale,
          localizationsDelegates: testLocalizationDelegates,
          supportedLocales: testSupportedLocales,
          home: const AcceptInvitePage(token: 'tok'),
        ),
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(container.read(pendingInviteTokenProvider), 'tok');
    expect(find.text('This invite has expired.'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });
}
