class PlanPackage {
  const PlanPackage({
    required this.id,
    required this.monthlyPriceCents,
    required this.deviceLimit,
    required this.historyDays,
    required this.storageGb,
    required this.realtimeAlerts,
    required this.clips,
    required this.prioritySupport,
  });

  final String id;
  final int monthlyPriceCents;
  final int deviceLimit;
  final int historyDays;
  final int storageGb;
  final bool realtimeAlerts;
  final bool clips;
  final bool prioritySupport;
}

class PlanPaymentMethod {
  const PlanPaymentMethod({
    required this.brand,
    required this.last4,
    required this.expiresMonth,
    required this.expiresYear,
  });

  final String brand;
  final String last4;
  final int expiresMonth;
  final int expiresYear;
}

class PlanInvoice {
  const PlanInvoice({
    required this.id,
    required this.issuedOn,
    required this.amountCents,
    required this.status,
    required this.packageId,
  });

  final String id;
  final String issuedOn;
  final int amountCents;
  final String status;
  final String packageId;
}

class UserPlan {
  const UserPlan({
    required this.currentPackageId,
    required this.renewsOn,
    required this.devicesInUse,
    required this.storageUsedGb,
    required this.paymentMethod,
    required this.packages,
    required this.invoices,
  });

  final String currentPackageId;
  final String renewsOn;
  final int devicesInUse;
  final double storageUsedGb;
  final PlanPaymentMethod paymentMethod;
  final List<PlanPackage> packages;
  final List<PlanInvoice> invoices;
}

const _packages = [
  PlanPackage(
    id: 'essential',
    monthlyPriceCents: 2990,
    deviceLimit: 1,
    historyDays: 7,
    storageGb: 10,
    realtimeAlerts: true,
    clips: false,
    prioritySupport: false,
  ),
  PlanPackage(
    id: 'family',
    monthlyPriceCents: 4990,
    deviceLimit: 3,
    historyDays: 30,
    storageGb: 50,
    realtimeAlerts: true,
    clips: true,
    prioritySupport: false,
  ),
  PlanPackage(
    id: 'home',
    monthlyPriceCents: 8990,
    deviceLimit: 8,
    historyDays: 90,
    storageGb: 200,
    realtimeAlerts: true,
    clips: true,
    prioritySupport: true,
  ),
];

UserPlan mockUserPlan() {
  return const UserPlan(
    currentPackageId: 'family',
    renewsOn: '2026-11-12',
    devicesInUse: 2,
    storageUsedGb: 18.4,
    paymentMethod: PlanPaymentMethod(
      brand: 'Visa',
      last4: '4242',
      expiresMonth: 8,
      expiresYear: 2028,
    ),
    packages: _packages,
    invoices: [
      PlanInvoice(
        id: 'inv-2026-10',
        issuedOn: '2026-10-12',
        amountCents: 4990,
        status: 'paid',
        packageId: 'family',
      ),
      PlanInvoice(
        id: 'inv-2026-09',
        issuedOn: '2026-09-12',
        amountCents: 4990,
        status: 'paid',
        packageId: 'family',
      ),
      PlanInvoice(
        id: 'inv-2026-08',
        issuedOn: '2026-08-12',
        amountCents: 2990,
        status: 'paid',
        packageId: 'essential',
      ),
    ],
  );
}
