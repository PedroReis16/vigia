import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/presentation/user/pages/auth_page.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';
import 'package:vigia_ui/presentation/user/providers/cold_start_provider.dart';

import '../../helpers/pump_app.dart';

class _LoggedOutSession extends AuthSession {
  @override
  Future<bool> build() async => false;
}

class _ColdStartDone extends ColdStartCompleted {
  @override
  bool build() => true;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'AuthPage shows the logo and Entrar when the session is logged out',
    (tester) async {
      await pumpApp(
        tester,
        locale: const Locale('pt'),
        overrides: [
          authSessionProvider.overrideWith(_LoggedOutSession.new),
          coldStartCompletedProvider.overrideWith(_ColdStartDone.new),
        ],
        child: const AuthPage(),
      );

      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('auth-enter')), findsOneWidget);
      expect(find.text('Entrar'), findsOneWidget);
      expect(find.text('Email'), findsNothing);
      expect(find.text('Password'), findsNothing);
    },
  );
}
