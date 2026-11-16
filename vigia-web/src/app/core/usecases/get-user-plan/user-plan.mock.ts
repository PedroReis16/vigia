import { PlanInvoice, PlanPackage, PlanPaymentMethod, UserPlan } from '@core/entities';

const packages: readonly PlanPackage[] = [
  new PlanPackage(
    'essential',
    'PROFILE.PLAN.CATALOG.ESSENTIAL.NAME',
    'PROFILE.PLAN.CATALOG.ESSENTIAL.HINT',
    2990,
    1,
    7,
    10,
    true,
    false,
    false,
  ),
  new PlanPackage(
    'family',
    'PROFILE.PLAN.CATALOG.FAMILY.NAME',
    'PROFILE.PLAN.CATALOG.FAMILY.HINT',
    4990,
    3,
    30,
    50,
    true,
    true,
    false,
  ),
  new PlanPackage(
    'home',
    'PROFILE.PLAN.CATALOG.HOME.NAME',
    'PROFILE.PLAN.CATALOG.HOME.HINT',
    8990,
    8,
    90,
    200,
    true,
    true,
    true,
  ),
];

export function mockUserPlan(): UserPlan {
  return new UserPlan(
    'active',
    'family',
    '2026-11-12',
    2,
    18.4,
    new PlanPaymentMethod('Visa', '4242', 8, 2028),
    packages,
    [
      new PlanInvoice('inv-2026-10', '2026-10-12', 4990, 'paid', 'family'),
      new PlanInvoice('inv-2026-09', '2026-09-12', 4990, 'paid', 'family'),
      new PlanInvoice('inv-2026-08', '2026-08-12', 2990, 'paid', 'essential'),
    ],
  );
}
