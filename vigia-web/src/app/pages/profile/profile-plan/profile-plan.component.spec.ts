import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { ProfilePlanComponent } from './profile-plan.component';

describe('ProfilePlanComponent', () => {
  let fixture: ComponentFixture<ProfilePlanComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfilePlanComponent, TranslateModule.forRoot()],
      providers: [
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfilePlanComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('shows the sample family plan, card and payment history', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('[data-testid="profile-plan-name"]')?.textContent).toContain(
      'PROFILE.PLAN.CATALOG.FAMILY.NAME',
    );
    expect(compiled.querySelector('[data-testid="profile-plan-price"]')?.textContent).toMatch(
      /49,90/,
    );
    expect(compiled.querySelector('[data-testid="profile-plan-card"]')?.textContent).toContain(
      '4242',
    );
    expect(compiled.querySelectorAll('[data-testid="profile-plan-invoice"]')).toHaveLength(4);
    expect(compiled.querySelector('[data-testid="profile-plan-active"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="profile-plan-edit"]')).toBeNull();
    expect(compiled.querySelector('[data-testid="profile-plan-draft"]')).toBeNull();
    expect(compiled.querySelector('[data-testid="profile-plan-over-limit"]')).toBeNull();
  });
});
