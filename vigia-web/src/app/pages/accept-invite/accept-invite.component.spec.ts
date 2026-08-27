import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter, Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { AcceptShareInviteService } from '@core/usecases';
import { MessageService, PendingInviteService } from '@core/services';
import { AcceptInviteComponent } from './accept-invite.component';

describe('AcceptInviteComponent', () => {
  let component: AcceptInviteComponent;
  let fixture: ComponentFixture<AcceptInviteComponent>;
  let acceptInvite: { execute: ReturnType<typeof vi.fn> };
  let pendingInvite: { clear: ReturnType<typeof vi.fn> };
  let messageService: MessageService;
  let router: Router;

  beforeEach(async () => {
    acceptInvite = { execute: vi.fn().mockResolvedValue(undefined) };
    pendingInvite = { clear: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [AcceptInviteComponent, TranslateModule.forRoot()],
      providers: [
        { provide: AcceptShareInviteService, useValue: acceptInvite },
        { provide: PendingInviteService, useValue: pendingInvite },
        MessageService,
        provideRouter([{ path: 'devices', children: [] }]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: () => 'invite-token' } },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AcceptInviteComponent);
    component = fixture.componentInstance;
    messageService = TestBed.inject(MessageService);
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('accepts invite and navigates to devices on success', async () => {
    fixture.detectChanges();
    await fixture.whenStable();

    expect(acceptInvite.execute).toHaveBeenCalledWith('invite-token');
    expect(pendingInvite.clear).toHaveBeenCalled();
    expect(messageService.getMessages()()?.type).toBe('success');
    expect(router.navigateByUrl).toHaveBeenCalledWith('/devices');
  });

  it('shows error and navigates to devices on failure', async () => {
    acceptInvite.execute.mockRejectedValue(new Error('failed'));
    fixture.detectChanges();
    await fixture.whenStable();

    expect(messageService.getMessages()()?.type).toBe('error');
    expect(router.navigateByUrl).toHaveBeenCalledWith('/devices');
  });
});
