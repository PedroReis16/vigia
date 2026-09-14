import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/presentation/user/pages/auth_page.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';
import 'package:vigia_ui/presentation/user/providers/cold_start_provider.dart';
import 'package:vigia_ui/presentation/user/widgets/login_form_widget.dart';

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
    'AuthPage shows login form when session is logged out and cold start done',
    (tester) async {
      await pumpApp(
        tester,
        overrides: [
          authSessionProvider.overrideWith(_LoggedOutSession.new),
          coldStartCompletedProvider.overrideWith(_ColdStartDone.new),
        ],
        child: const AuthPage(),
      );

      // Warm-up + first frames; intro starts already at progress 1.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      await tester.pumpAndSettle();

      expect(find.byType(LoginForm), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.text('Sign in'), findsWidgets);
      expect(find.text("Don't have an account?"), findsOneWidget);
    },
  );
}
