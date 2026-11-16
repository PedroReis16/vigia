import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/presentation/settings/widgets/profile_plan_card.dart';

import '../../helpers/pump_app.dart';

void main() {
  testWidgets('shows the active family plan preview', (tester) async {
    await pumpApp(
      tester,
      child: const SingleChildScrollView(child: ProfilePlanCard()),
    );

    expect(find.text('Plan'), findsOneWidget);
    expect(find.text('Active plan'), findsOneWidget);
    expect(find.text('Family care'), findsWidgets);
    expect(find.text('Visa •••• 4242'), findsOneWidget);
    expect(find.text('3 devices'), findsOneWidget);
    expect(find.text('Fall clips'), findsOneWidget);
    expect(find.text('Priority support'), findsNothing);
    expect(find.text('Payments'), findsOneWidget);
    expect(find.text('Scheduled'), findsOneWidget);
    expect(find.text('Essential'), findsOneWidget);
  });
}
