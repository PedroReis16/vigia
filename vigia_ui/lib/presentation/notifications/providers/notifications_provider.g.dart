// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'notifications_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(NotificationsInbox)
final notificationsInboxProvider = NotificationsInboxProvider._();

final class NotificationsInboxProvider
    extends $AsyncNotifierProvider<NotificationsInbox, NotificationInbox> {
  NotificationsInboxProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'notificationsInboxProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$notificationsInboxHash();

  @$internal
  @override
  NotificationsInbox create() => NotificationsInbox();
}

String _$notificationsInboxHash() =>
    r'080b1deb9a79d8f7e0facea59521ac9f9f20f84b';

abstract class _$NotificationsInbox extends $AsyncNotifier<NotificationInbox> {
  FutureOr<NotificationInbox> build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref =
        this.ref as $Ref<AsyncValue<NotificationInbox>, NotificationInbox>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<NotificationInbox>, NotificationInbox>,
              AsyncValue<NotificationInbox>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
