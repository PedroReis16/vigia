import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/presentation/devices/widgets/connect_stage_widgets/status_view.dart';
import 'package:vigia_ui/presentation/devices/widgets/connect_stage_widgets/step_tile.dart';
import 'package:vigia_ui/presentation/user/widgets/devices_load_erro.dart';

import '../../helpers/pump_app.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('DevicesLoadError', () {
    testWidgets('shows message and try again action', (tester) async {
      var tried = false;

      await pumpApp(
        tester,
        child: Scaffold(
          body: DevicesLoadError(onTryAgain: () => tried = true),
        ),
      );
      await tester.pumpAndSettle();

      expect(
        find.text("It looks like we're experiencing technical issues."),
        findsOneWidget,
      );
      expect(find.text('Try again'), findsOneWidget);

      await tester.tap(find.text('Try again'));
      expect(tried, isTrue);
    });
  });

  group('StepTile', () {
    testWidgets('shows step number, title, and description', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StepTile(
              number: 2,
              title: 'Connect Wi-Fi',
              description: 'Join the device hotspot',
            ),
          ),
        ),
      );

      expect(find.text('2'), findsOneWidget);
      expect(find.text('Connect Wi-Fi'), findsOneWidget);
      expect(find.text('Join the device hotspot'), findsOneWidget);
    });
  });

  group('StatusView', () {
    testWidgets('shows localized header, title, description, and action', (
      tester,
    ) async {
      await pumpApp(
        tester,
        child: Scaffold(
          body: SizedBox(
            height: 600,
            child: StatusView(
              icon: const Icon(Icons.check),
              title: 'Ready',
              description: 'Device is online',
              action: ElevatedButton(
                onPressed: () {},
                child: const Text('Continue'),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Add device'), findsOneWidget);
      expect(find.text('Ready'), findsOneWidget);
      expect(find.text('Device is online'), findsOneWidget);
      expect(find.text('Continue'), findsOneWidget);
      expect(find.byIcon(Icons.check), findsOneWidget);
    });
  });
}
