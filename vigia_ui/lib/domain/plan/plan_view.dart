import 'package:intl/intl.dart';
import 'package:vigia_ui/domain/plan/user_plan.dart';

enum PlanFeatureKey {
  device,
  devices,
  history,
  storage,
  alerts,
  clips,
  priority,
}

class PlanFeatureView {
  const PlanFeatureView(this.key, {this.count, this.days, this.gb});

  final PlanFeatureKey key;
  final int? count;
  final int? days;
  final int? gb;
}

class PlanUsageView {
  const PlanUsageView({
    required this.id,
    required this.usedLabel,
    required this.limitLabel,
    required this.percent,
    required this.overLimit,
  });

  final String id;
  final String usedLabel;
  final String limitLabel;
  final int percent;
  final bool overLimit;
}

class PlanInvoiceView {
  const PlanInvoiceView({
    required this.id,
    required this.dateLabel,
    required this.packageId,
    required this.amountLabel,
    required this.status,
  });

  final String id;
  final String dateLabel;
  final String packageId;
  final String amountLabel;
  final String status;
}

class PlanView {
  const PlanView({
    required this.packageId,
    required this.priceLabel,
    required this.renewalLabel,
    required this.cardLabel,
    required this.expiryLabel,
    required this.usages,
    required this.features,
    required this.invoices,
  });

  final String packageId;
  final String priceLabel;
  final String renewalLabel;
  final String cardLabel;
  final String expiryLabel;
  final List<PlanUsageView> usages;
  final List<PlanFeatureView> features;
  final List<PlanInvoiceView> invoices;
}

String planLocale(String languageCode) {
  return switch (languageCode) {
    'en' => 'en',
    'es' => 'es',
    _ => 'pt',
  };
}

PlanView buildPlanView(UserPlan plan, String packageId, String locale) {
  final selected =
      _packageById(plan, packageId) ??
      _packageById(plan, plan.currentPackageId);
  if (selected == null) {
    throw StateError('Unknown plan package: $packageId');
  }

  final resolved = planLocale(locale);
  return PlanView(
    packageId: selected.id,
    priceLabel: formatPlanMoney(selected.monthlyPriceCents, resolved),
    renewalLabel: formatPlanDate(plan.renewsOn, resolved),
    cardLabel: '${plan.paymentMethod.brand} •••• ${plan.paymentMethod.last4}',
    expiryLabel:
        '${plan.paymentMethod.expiresMonth.toString().padLeft(2, '0')}/${plan.paymentMethod.expiresYear}',
    usages: [
      _usage(
        id: 'devices',
        used: plan.devicesInUse.toDouble(),
        limit: selected.deviceLimit.toDouble(),
        usedLabel: '${plan.devicesInUse}',
        limitLabel: '${selected.deviceLimit}',
      ),
      _usage(
        id: 'storage',
        used: plan.storageUsedGb,
        limit: selected.storageGb.toDouble(),
        usedLabel: formatPlanQuantity(plan.storageUsedGb, resolved),
        limitLabel: formatPlanQuantity(selected.storageGb.toDouble(), resolved),
      ),
    ],
    features: _featuresOf(selected),
    invoices: _invoicesOf(plan, selected, resolved),
  );
}

String formatPlanMoney(int cents, String locale) {
  return NumberFormat.simpleCurrency(
    name: 'BRL',
    locale: planLocale(locale),
  ).format(cents / 100);
}

String formatPlanQuantity(double value, String locale) {
  final format = NumberFormat.decimalPattern(planLocale(locale))
    ..maximumFractionDigits = 1;
  return format.format(value);
}

String formatPlanDate(String isoDate, String locale) {
  final parts = isoDate.split('-').map(int.parse).toList();
  final date = DateTime(parts[0], parts[1], parts[2]);
  return DateFormat.yMMMd(planLocale(locale)).format(date);
}

PlanPackage? _packageById(UserPlan plan, String id) {
  for (final item in plan.packages) {
    if (item.id == id) return item;
  }
  return null;
}

List<PlanFeatureView> _featuresOf(PlanPackage planPackage) {
  final features = <PlanFeatureView>[
    planPackage.deviceLimit == 1
        ? const PlanFeatureView(PlanFeatureKey.device)
        : PlanFeatureView(
            PlanFeatureKey.devices,
            count: planPackage.deviceLimit,
          ),
    PlanFeatureView(PlanFeatureKey.history, days: planPackage.historyDays),
    PlanFeatureView(PlanFeatureKey.storage, gb: planPackage.storageGb),
  ];
  if (planPackage.realtimeAlerts) {
    features.add(const PlanFeatureView(PlanFeatureKey.alerts));
  }
  if (planPackage.clips) {
    features.add(const PlanFeatureView(PlanFeatureKey.clips));
  }
  if (planPackage.prioritySupport) {
    features.add(const PlanFeatureView(PlanFeatureKey.priority));
  }
  return features;
}

List<PlanInvoiceView> _invoicesOf(
  UserPlan plan,
  PlanPackage selected,
  String locale,
) {
  final upcoming = PlanInvoiceView(
    id: 'upcoming',
    dateLabel: formatPlanDate(plan.renewsOn, locale),
    packageId: selected.id,
    amountLabel: formatPlanMoney(selected.monthlyPriceCents, locale),
    status: 'scheduled',
  );
  final history = [...plan.invoices]
    ..sort((left, right) => right.issuedOn.compareTo(left.issuedOn));
  return [
    upcoming,
    ...history.map(
      (invoice) => PlanInvoiceView(
        id: invoice.id,
        dateLabel: formatPlanDate(invoice.issuedOn, locale),
        packageId: invoice.packageId,
        amountLabel: formatPlanMoney(invoice.amountCents, locale),
        status: invoice.status,
      ),
    ),
  ];
}

PlanUsageView _usage({
  required String id,
  required double used,
  required double limit,
  required String usedLabel,
  required String limitLabel,
}) {
  final ratio = limit <= 0 ? 1.0 : used / limit;
  final percent = (ratio * 100).round().clamp(0, 100);
  return PlanUsageView(
    id: id,
    usedLabel: usedLabel,
    limitLabel: limitLabel,
    percent: percent,
    overLimit: used > limit,
  );
}
