import { Injectable } from '@angular/core';
import { UserPlan } from '@core/entities';
import { mockUserPlan } from './user-plan.mock';

@Injectable({
  providedIn: 'root',
})
export class GetUserPlanService {
  execute(): Promise<UserPlan> {
    return Promise.resolve(mockUserPlan());
  }
}
