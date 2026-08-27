import { AfterViewInit, Component, EventEmitter, forwardRef, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputTextModule } from '@openng/optimus-ui/inputtext';
import { InputMask } from '@openng/optimus-ui/inputmask';
import { DatePicker } from '@openng/optimus-ui/datepicker';
import { TranslateModule } from '@ngx-translate/core';
import {
  FormsModule,
  ReactiveFormsModule,
  FormControl,
  ControlValueAccessor,
  NG_VALUE_ACCESSOR,
} from '@angular/forms';
import { Select } from '@openng/optimus-ui/select';
import { Password } from '@openng/optimus-ui/password';
import { Skeleton } from '@openng/optimus-ui/skeleton';
import { InputNumber } from '@openng/optimus-ui/inputnumber';
import { Textarea } from '@openng/optimus-ui/textarea';
import moment from 'moment';

@Component({
  selector: 'app-input',
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    InputTextModule,
    InputMask,
    DatePicker,
    TranslateModule,
    Select,
    Password,
    Skeleton,
    InputNumber,
    Textarea,
  ],
  templateUrl: './input.component.html',
  styleUrl: './input.component.css',
  standalone: true,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => InputComponent),
      multi: true,
    },
  ],
})
export class InputComponent implements ControlValueAccessor, AfterViewInit {
  @Input() label: string = '';
  @Input() id: string = '';
  @Input() type: 'text' | 'mask' | 'dropdown' | 'calendar' | 'password' | 'number' | 'textarea' =
    'text';
  @Input() mask?: string;
  @Input() options?: any[];
  @Input() readonly?: boolean = false;
  @Input() control!: FormControl;
  @Input() isLoading: boolean = false;
  @Input() pSize: 'small' | 'large' = 'small';
  @Input() value: any = '';
  @Input() enableDropdownFilter: boolean = false;
  @Input() maxLength?: number;
  @Input() minLength?: number;
  @Input() max?: number;
  @Input() min?: number;
  @Input() error?: string;
  @Output() valueChange = new EventEmitter<any>();
  @Output() valueModelChange = new EventEmitter<any>();

  onChange?: (value: any) => void;
  onTouched?: () => void;
  disabled = false;

  ngAfterViewInit(): void {
    console.log(this.label);
    console.log(this.value);
  }

  onTextValueChange(event: any) {
    const rawValue = event?.target?.value ?? event?.value ?? event;
    const returnValue = {
      value: rawValue,
      type: 'text',
    };

    if (this.type === 'mask' && this.mask) {
      const regexPattern = this.convertMaskToRegex(this.mask);
      const regex = new RegExp(regexPattern);

      if (!regex.test(returnValue.value)) {
        return;
      }
    }

    this.valueChange.emit(returnValue);
    this.valueModelChange.emit(returnValue);

    if (this.onChange) {
      this.onChange(returnValue.value);
    }
  }

  private convertMaskToRegex(mask: string): string {
    return mask
      .replace(/9/g, '\\d')
      .replace(/A/g, '[A-Za-z]')
      .replace(/S/g, '[A-Za-z0-9]')
      .replace(/\./g, '\\.')
      .replace(/-/g, '\\-')
      .replace(/\//g, '\\/');
  }

  onDropdownValueChange(event: any) {
    const returnValue = {
      value: event.value,
      type: 'dropdown',
    };

    this.valueChange.emit(returnValue);
    this.valueModelChange.emit(returnValue);

    if (this.onChange) {
      this.onChange(returnValue.value);
    }
  }

  onCalendarValueChange(event: any) {
    const returnValue = {
      value: event,
      type: 'calendar',
    };

    if (event && event.target) {
      const momentDate = moment(event.target.value, 'DD/MM/YYYY');
      if (!momentDate.isValid()) {
        return;
      }

      returnValue.value = momentDate.toDate();
    }

    this.valueChange.emit(returnValue);
    this.valueModelChange.emit(returnValue);

    if (this.onChange) {
      this.onChange(returnValue.value);
    }
  }

  writeValue(obj: any): void {
    this.value = obj;
  }
  registerOnChange(fn: any): void {
    this.onChange = fn;
  }
  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }
  setDisabledState?(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
