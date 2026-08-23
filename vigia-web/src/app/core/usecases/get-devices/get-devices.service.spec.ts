import { TestBed } from '@angular/core/testing';
import { GetDevicesService } from './get-devices.service';

describe('GetDevicesService', () => {
  let service: GetDevicesService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(GetDevicesService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
