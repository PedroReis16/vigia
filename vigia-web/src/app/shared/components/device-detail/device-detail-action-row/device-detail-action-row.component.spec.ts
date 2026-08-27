import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { DeviceDetailActionRowComponent } from './device-detail-action-row.component';

describe('DeviceDetailActionRowComponent', () => {
  let fixture: ComponentFixture<DeviceDetailActionRowComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DeviceDetailActionRowComponent, TranslateModule.forRoot()],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(DeviceDetailActionRowComponent);
    fixture.componentRef.setInput('icon', 'pi pi-pencil');
    fixture.componentRef.setInput('title', 'DEVICES.EDIT.TITLE');
    fixture.detectChanges();
  });

  it('renders as a button and emits action when clicked', () => {
    const action = vi.fn();
    fixture.componentInstance.action.subscribe(action);

    const button = fixture.nativeElement.querySelector('button.device-detail-action-row');
    expect(button).toBeTruthy();

    button.click();
    expect(action).toHaveBeenCalledTimes(1);
  });

  it('renders as a link when routerLink is provided', () => {
    fixture.componentRef.setInput('routerLink', '/devices/1/clips');
    fixture.detectChanges();

    const link = fixture.nativeElement.querySelector('a.device-detail-action-row');
    expect(link).toBeTruthy();
    expect(link.getAttribute('href')).toContain('/devices/1/clips');
  });

  it('does not emit action when disabled', () => {
    const action = vi.fn();
    fixture.componentInstance.action.subscribe(action);
    fixture.componentRef.setInput('disabled', true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button.device-detail-action-row');
    button.click();
    expect(action).not.toHaveBeenCalled();
  });
});
