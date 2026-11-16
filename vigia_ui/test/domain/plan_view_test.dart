import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:vigia_ui/domain/plan/plan_view.dart';
import 'package:vigia_ui/domain/plan/user_plan.dart';

void main() {
  setUpAll(() async {
    await initializeDateFormatting('pt');
    await initializeDateFormatting('en');
  });

  final plan = mockUserPlan();

  test('describes the current family package in Portuguese', () {
    final view = buildPlanView(plan, plan.currentPackageId, 'pt');

    expect(view.packageId, 'family');
    expect(view.priceLabel.replaceAll(RegExp(r'\s'), ' '), contains('49,90'));
    expect(view.cardLabel, 'Visa •••• 4242');
    expect(view.expiryLabel, '08/2028');
    expect(view.usages.every((item) => !item.overLimit), isTrue);
    expect(view.invoices.first.status, 'scheduled');
    expect(
      view.invoices.first.amountLabel.replaceAll(RegExp(r'\s'), ' '),
      contains('49,90'),
    );
    expect(view.invoices.last.packageId, 'essential');
    expect(view.renewalLabel, contains('2026'));
  });

  test(
    'marks usage over the essential limits and reprices the next charge',
    () {
      final view = buildPlanView(plan, 'essential', 'pt');

      expect(view.packageId, 'essential');
      expect(view.usages.every((item) => item.overLimit), isTrue);
      expect(
        view.features.any((item) => item.key == PlanFeatureKey.clips),
        isFalse,
      );
      expect(
        view.invoices.first.amountLabel.replaceAll(RegExp(r'\s'), ' '),
        contains('29,90'),
      );
      expect(
        view.invoices[1].amountLabel.replaceAll(RegExp(r'\s'), ' '),
        contains('49,90'),
      );
    },
  );

  test('includes priority support on the residential package', () {
    final view = buildPlanView(plan, 'home', 'en');

    expect(view.features.last.key, PlanFeatureKey.priority);
    expect(view.priceLabel.replaceAll(RegExp(r'\s'), ' '), contains('89.90'));
  });

  test('falls back to the current package when the id is unknown', () {
    final view = buildPlanView(plan, 'missing', 'pt');

    expect(view.packageId, 'family');
  });
}
