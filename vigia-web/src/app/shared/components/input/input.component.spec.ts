import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { VigiaTheme } from '@shared/theme/vigia.theme';

import { InputComponent } from './input.component';

describe('InputComponent', () => {
  let component: InputComponent;
  let fixture: ComponentFixture<InputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InputComponent, TranslateModule.forRoot()],
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

    fixture = TestBed.createComponent(InputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render an Optimus text input', () => {
    const input = fixture.nativeElement.querySelector('input[pinputtext]');
    expect(input).toBeTruthy();
  });
});
