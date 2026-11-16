export type UserPlanStatus = 'active';
export type PlanInvoiceStatus = 'paid' | 'scheduled';

export class PlanPackage {
  constructor(
    public readonly id: string,
    public readonly nameKey: string,
    public readonly hintKey: string,
    public readonly monthlyPriceCents: number,
    public readonly deviceLimit: number,
    public readonly historyDays: number,
    public readonly storageGb: number,
    public readonly realtimeAlerts: boolean,
    public readonly clips: boolean,
    public readonly prioritySupport: boolean,
  ) {}
}

export class PlanPaymentMethod {
  constructor(
    public readonly brand: string,
    public readonly last4: string,
    public readonly expiresMonth: number,
    public readonly expiresYear: number,
  ) {}
}

export class PlanInvoice {
  constructor(
    public readonly id: string,
    public readonly issuedOn: string,
    public readonly amountCents: number,
    public readonly status: PlanInvoiceStatus,
    public readonly packageId: string,
  ) {}
}

export class UserPlan {
  constructor(
    public readonly status: UserPlanStatus,
    public readonly currentPackageId: string,
    public readonly renewsOn: string,
    public readonly devicesInUse: number,
    public readonly storageUsedGb: number,
    public readonly paymentMethod: PlanPaymentMethod,
    public readonly packages: readonly PlanPackage[],
    public readonly invoices: readonly PlanInvoice[],
  ) {}
}
