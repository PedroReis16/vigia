import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';

void main() {
  group('AppLoadingIndicator', () {
    testWidgets('shows CircularProgressIndicator', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: Scaffold(body: AppLoadingIndicator())),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.byType(SizedBox), findsNothing);
    });

    testWidgets('wraps indicator in SizedBox when size is set', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: Scaffold(body: AppLoadingIndicator(size: 48))),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      final sizedBox = tester.widget<SizedBox>(find.byType(SizedBox));
      expect(sizedBox.width, 48);
      expect(sizedBox.height, 48);
    });
  });
}
