import { mockUserPlan } from '@core/usecases/get-user-plan/user-plan.mock';
import { buildPlanView } from './plan-view.helper';

describe('buildPlanView', () => {
  const plan = mockUserPlan();

  it('describes the current family package in Portuguese', () => {
    const view = buildPlanView(plan, plan.currentPackageId, 'pt-BR');

    expect(view.nameKey).toBe('PROFILE.PLAN.CATALOG.FAMILY.NAME');
    expect(view.priceLabel.replace(/\s/g, ' ')).toContain('49,90');
    expect(view.cardLabel).toBe('Visa •••• 4242');
    expect(view.expiryLabel).toBe('08/2028');
    expect(view.packages.find((item) => item.actual)?.id).toBe('family');
    expect(view.usages.every((item) => !item.overLimit)).toBe(true);
    expect(view.invoices[0]?.status).toBe('scheduled');
    expect(view.invoices[0]?.amountLabel.replace(/\s/g, ' ')).toContain('49,90');
    expect(view.invoices.at(-1)?.packageNameKey).toBe('PROFILE.PLAN.CATALOG.ESSENTIAL.NAME');
  });

  it('marks usage over the essential limits and reprices the next charge', () => {
    const view = buildPlanView(plan, 'essential', 'pt-BR');

    expect(view.nameKey).toBe('PROFILE.PLAN.CATALOG.ESSENTIAL.NAME');
    expect(view.usages.every((item) => item.overLimit)).toBe(true);
    expect(view.features.some((item) => item.key === 'PROFILE.PLAN.FEATURES.CLIPS')).toBe(false);
    expect(view.invoices[0]?.amountLabel.replace(/\s/g, ' ')).toContain('29,90');
    expect(view.invoices[1]?.amountLabel.replace(/\s/g, ' ')).toContain('49,90');
    expect(view.packages.find((item) => item.id === 'family')?.actual).toBe(true);
    expect(view.packages.find((item) => item.id === 'essential')?.selected).toBe(true);
  });

  it('includes priority support on the residential package', () => {
    const view = buildPlanView(plan, 'home', 'en-US');

    expect(view.features.at(-1)?.key).toBe('PROFILE.PLAN.FEATURES.PRIORITY');
    expect(view.priceLabel.replace(/\s/g, ' ')).toContain('89.90');
  });

  it('falls back to the current package when the id is unknown', () => {
    const view = buildPlanView(plan, 'missing', 'pt-BR');

    expect(view.nameKey).toBe('PROFILE.PLAN.CATALOG.FAMILY.NAME');
  });
});
