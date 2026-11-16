import { PlanInvoiceStatus, PlanPackage, UserPlan, UserPlanStatus } from '@core/entities';

export interface PlanFeatureView {
  key: string;
  params?: Record<string, string | number>;
}

export interface PlanUsageView {
  id: 'devices' | 'storage';
  labelKey: string;
  usedLabel: string;
  limitLabel: string;
  percent: number;
  overLimit: boolean;
  used: number;
  limit: number;
}

export interface PlanPackageView {
  id: string;
  nameKey: string;
  hintKey: string;
  priceLabel: string;
  selected: boolean;
  actual: boolean;
}

export interface PlanInvoiceView {
  id: string;
  dateLabel: string;
  packageNameKey: string;
  amountLabel: string;
  status: PlanInvoiceStatus;
  statusKey: string;
}

export interface PlanView {
  nameKey: string;
  priceLabel: string;
  renewalLabel: string;
  status: UserPlanStatus;
  cardLabel: string;
  expiryLabel: string;
  usages: readonly PlanUsageView[];
  features: readonly PlanFeatureView[];
  packages: readonly PlanPackageView[];
  invoices: readonly PlanInvoiceView[];
}

export function buildPlanView(plan: UserPlan, packageId: string, locale: string): PlanView {
  const selected =
    plan.packages.find((item) => item.id === packageId) ?? packageById(plan, plan.currentPackageId);
  const resolvedLocale = normalizeLocale(locale);

  return {
    nameKey: selected.nameKey,
    priceLabel: formatPlanMoney(selected.monthlyPriceCents, resolvedLocale),
    renewalLabel: formatPlanDate(plan.renewsOn, resolvedLocale),
    status: plan.status,
    cardLabel: `${plan.paymentMethod.brand} •••• ${plan.paymentMethod.last4}`,
    expiryLabel: `${String(plan.paymentMethod.expiresMonth).padStart(2, '0')}/${plan.paymentMethod.expiresYear}`,
    usages: [
      usage(
        'devices',
        'PROFILE.PLAN.USAGE_DEVICES',
        plan.devicesInUse,
        selected.deviceLimit,
        String(plan.devicesInUse),
        String(selected.deviceLimit),
      ),
      usage(
        'storage',
        'PROFILE.PLAN.USAGE_STORAGE',
        plan.storageUsedGb,
        selected.storageGb,
        formatQuantity(plan.storageUsedGb, resolvedLocale),
        formatQuantity(selected.storageGb, resolvedLocale),
      ),
    ],
    features: featuresOf(selected),
    packages: plan.packages.map((item) => ({
      id: item.id,
      nameKey: item.nameKey,
      hintKey: item.hintKey,
      priceLabel: formatPlanMoney(item.monthlyPriceCents, resolvedLocale),
      selected: item.id === selected.id,
      actual: item.id === plan.currentPackageId,
    })),
    invoices: invoicesOf(plan, selected, resolvedLocale),
  };
}

function packageById(plan: UserPlan, id: string): PlanPackage {
  const found = plan.packages.find((item) => item.id === id);
  if (!found) {
    throw new Error(`Unknown plan package: ${id}`);
  }
  return found;
}

function featuresOf(planPackage: PlanPackage): PlanFeatureView[] {
  const features: PlanFeatureView[] = [
    {
      key:
        planPackage.deviceLimit === 1
          ? 'PROFILE.PLAN.FEATURES.DEVICE'
          : 'PROFILE.PLAN.FEATURES.DEVICES',
      params: { count: planPackage.deviceLimit },
    },
    { key: 'PROFILE.PLAN.FEATURES.HISTORY', params: { days: planPackage.historyDays } },
    { key: 'PROFILE.PLAN.FEATURES.STORAGE', params: { gb: planPackage.storageGb } },
  ];

  if (planPackage.realtimeAlerts) {
    features.push({ key: 'PROFILE.PLAN.FEATURES.ALERTS' });
  }
  if (planPackage.clips) {
    features.push({ key: 'PROFILE.PLAN.FEATURES.CLIPS' });
  }
  if (planPackage.prioritySupport) {
    features.push({ key: 'PROFILE.PLAN.FEATURES.PRIORITY' });
  }

  return features;
}

function invoicesOf(plan: UserPlan, selected: PlanPackage, locale: string): PlanInvoiceView[] {
  const upcoming: PlanInvoiceView = {
    id: 'upcoming',
    dateLabel: formatPlanDate(plan.renewsOn, locale),
    packageNameKey: selected.nameKey,
    amountLabel: formatPlanMoney(selected.monthlyPriceCents, locale),
    status: 'scheduled',
    statusKey: 'PROFILE.PLAN.INVOICE_STATUS.SCHEDULED',
  };

  const history = [...plan.invoices]
    .sort((left, right) => right.issuedOn.localeCompare(left.issuedOn))
    .map((invoice) => ({
      id: invoice.id,
      dateLabel: formatPlanDate(invoice.issuedOn, locale),
      packageNameKey: packageById(plan, invoice.packageId).nameKey,
      amountLabel: formatPlanMoney(invoice.amountCents, locale),
      status: invoice.status,
      statusKey: `PROFILE.PLAN.INVOICE_STATUS.${invoice.status.toUpperCase()}`,
    }));

  return [upcoming, ...history];
}

function usage(
  id: PlanUsageView['id'],
  labelKey: string,
  used: number,
  limit: number,
  usedLabel: string,
  limitLabel: string,
): PlanUsageView {
  const ratio = limit <= 0 ? 1 : used / limit;
  return {
    id,
    labelKey,
    usedLabel,
    limitLabel,
    percent: Math.min(100, Math.round(ratio * 100)),
    overLimit: used > limit,
    used,
    limit,
  };
}

function formatPlanMoney(cents: number, locale: string): string {
  return new Intl.NumberFormat(locale, { style: 'currency', currency: 'BRL' }).format(cents / 100);
}

function formatQuantity(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(value);
}

function formatPlanDate(isoDate: string, locale: string): string {
  const [year, month, day] = isoDate.split('-').map(Number);
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(year, month - 1, day));
}

function normalizeLocale(locale: string): string {
  if (locale === 'pt-BR' || locale === 'en-US' || locale === 'es-ES') {
    return locale;
  }
  return 'pt-BR';
}
