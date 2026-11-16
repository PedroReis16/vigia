import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { UserProfileHttpService } from './user-profile-http.service';

describe('UserProfileHttpService', () => {
  let service: UserProfileHttpService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(UserProfileHttpService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('loads the profile from /users/me', () => {
    service.getProfile().subscribe();

    const req = httpMock.expectOne('/users/me');
    expect(req.request.method).toBe('GET');
    req.flush({ id: '1', name: 'Ana' });
  });

  it('uploads the picture as multipart file', () => {
    const file = new File([new Uint8Array([1])], 'avatar.jpg', { type: 'image/jpeg' });
    service.uploadPicture(file).subscribe();

    const req = httpMock.expectOne('/users/me/picture');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toBeInstanceOf(FormData);
    expect((req.request.body as FormData).get('file')).toBe(file);
    req.flush({ id: '1', name: 'Ana' });
  });

  it('removes the picture', () => {
    service.removePicture().subscribe();

    const req = httpMock.expectOne('/users/me/picture');
    expect(req.request.method).toBe('DELETE');
    req.flush({ id: '1', name: 'Ana', pictureUrl: null });
  });

  it('updates name and phone', () => {
    const body = { firstName: 'Ana', lastName: 'Souza', phone: '11988887777' };
    service.updateProfile(body).subscribe();

    const req = httpMock.expectOne('/users/me');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(body);
    req.flush({ id: '1', name: 'Ana Souza' });
  });

  it('deletes the account', () => {
    service.deleteAccount().subscribe();

    const req = httpMock.expectOne('/users/me');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
