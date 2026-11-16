import { TestBed } from '@angular/core/testing';
import { NavigationCancel, NavigationCancellationCode, Router, RoutesRecognized } from '@angular/router';
import { Subject } from 'rxjs';
import { vi } from 'vitest';
import { DevicePageTransitionService } from './device-page-transition.service';

describe('DevicePageTransitionService', () => {
  let events: Subject<unknown>;
  let url: string;
  let content: HTMLElement;
  let service: DevicePageTransitionService;

  beforeEach(() => {
    events = new Subject();
    url = '/devices/device-1';
    content = document.createElement('div');
    content.className = 'layout__content';
    document.body.appendChild(content);

    TestBed.configureTestingModule({
      providers: [
        {
          provide: Router,
          useValue: {
            events,
            get url() {
              return url;
            },
          },
        },
      ],
    });

    service = TestBed.inject(DevicePageTransitionService);
    service.install();
    service.install();
  });

  afterEach(() => {
    content.remove();
    delete document.documentElement.dataset['pageTransition'];
  });

  it('arms a forward transition when opening clips', () => {
    events.next(new RoutesRecognized(1, url, '/devices/device-1/clips', {} as never));

    expect(document.documentElement.dataset['pageTransition']).toBe('forward');
    expect(content.style.viewTransitionName).toBe('device-page');
  });

  it('keeps the transition until the view transition finishes', async () => {
    let resolveFinished: () => void = () => undefined;
    const finished = new Promise<void>((resolve) => {
      resolveFinished = resolve;
    });
    const skipTransition = vi.fn();

    service.onCreated(
      { skipTransition, finished },
      { url: [{ path: 'devices' }, { path: 'device-1' }], firstChild: null },
      {
        url: [{ path: 'devices' }, { path: 'device-1' }, { path: 'clips' }],
        firstChild: null,
      },
    );

    expect(skipTransition).not.toHaveBeenCalled();
    expect(document.documentElement.dataset['pageTransition']).toBe('forward');

    resolveFinished();
    await finished;

    expect(document.documentElement.dataset['pageTransition']).toBeUndefined();
    expect(content.style.viewTransitionName).toBe('');
  });

  it('skips the view transition for other navigations', () => {
    const skipTransition = vi.fn();
    service.onCreated(
      { skipTransition, finished: Promise.resolve() },
      { url: [{ path: 'devices' }], firstChild: null },
      { url: [{ path: 'devices' }, { path: 'device-1' }], firstChild: null },
    );

    expect(skipTransition).toHaveBeenCalledOnce();
    expect(content.style.viewTransitionName).toBe('');
  });

  it('clears a prepared transition when navigation is cancelled', () => {
    events.next(new RoutesRecognized(1, url, '/devices/device-1/clips', {} as never));
    events.next(new NavigationCancel(1, url, '', NavigationCancellationCode.SupersededByNewNavigation));

    expect(document.documentElement.dataset['pageTransition']).toBeUndefined();
    expect(content.style.viewTransitionName).toBe('');
  });
});
