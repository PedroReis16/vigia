import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { vi } from 'vitest';
import { PendingInviteService } from '@core/services';
import { BeginKeycloakAuthService } from '@core/usecases';
import { AuthComponent } from './auth.component';

describe('AuthComponent', () => {
  let beginAuth: { execute: ReturnType<typeof vi.fn> };
  let pendingInvite: { getPostAuthPath: ReturnType<typeof vi.fn> };

  async function create(mode: string | null): Promise<ComponentFixture<AuthComponent>> {
    beginAuth = { execute: vi.fn().mockResolvedValue(undefined) };
    pendingInvite = { getPostAuthPath: vi.fn(() => '/devices') };

    await TestBed.configureTestingModule({
      imports: [AuthComponent],
      providers: [
        { provide: BeginKeycloakAuthService, useValue: beginAuth },
        { provide: PendingInviteService, useValue: pendingInvite },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap(mode ? { mode } : {}) } },
        },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(AuthComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('redirects to Keycloak login', async () => {
    const fixture = await create(null);
    expect(fixture.nativeElement.querySelector('[data-testid="auth-page"]')).toBeTruthy();
    expect(beginAuth.execute).toHaveBeenCalledWith('login', '/devices');
  });

  it('redirects to Keycloak registration', async () => {
    await create('register');
    expect(beginAuth.execute).toHaveBeenCalledWith('register', '/devices');
  });
});
