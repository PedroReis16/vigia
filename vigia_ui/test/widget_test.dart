import 'package:flutter_test/flutter_test.dart';

import 'package:vigia_ui/app.dart';

void main() {
  testWidgets('contador incrementa ao tocar no FAB', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('0'), findsOneWidget);
    expect(find.text('1'), findsNothing);

    await tester.tap(find.byTooltip('Increment'));
    await tester.pump();

    expect(find.text('0'), findsNothing);
    expect(find.text('1'), findsOneWidget);
  });
}
