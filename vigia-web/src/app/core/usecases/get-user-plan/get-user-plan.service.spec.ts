import { TestBed } from '@angular/core/testing';
import { GetUserPlanService } from './get-user-plan.service';

describe('GetUserPlanService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({});
  });

  it('returns the sample family plan', async () => {
    const service = TestBed.inject(GetUserPlanService);
    const plan = await service.execute();

    expect(plan.currentPackageId).toBe('family');
    expect(plan.status).toBe('active');
    expect(plan.packages.map((item) => item.id)).toEqual(['essential', 'family', 'home']);
    expect(plan.paymentMethod.last4).toBe('4242');
    expect(plan.invoices).toHaveLength(3);
    expect(plan.devicesInUse).toBe(2);
  });
});
