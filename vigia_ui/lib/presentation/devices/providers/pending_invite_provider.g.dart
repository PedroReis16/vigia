// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pending_invite_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(PendingInviteToken)
final pendingInviteTokenProvider = PendingInviteTokenProvider._();

final class PendingInviteTokenProvider
    extends $NotifierProvider<PendingInviteToken, String?> {
  PendingInviteTokenProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'pendingInviteTokenProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$pendingInviteTokenHash();

  @$internal
  @override
  PendingInviteToken create() => PendingInviteToken();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(String? value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<String?>(value),
    );
  }
}

String _$pendingInviteTokenHash() =>
    r'14dfb0527ce6ae92403aed3203e4b95f764657bb';

abstract class _$PendingInviteToken extends $Notifier<String?> {
  String? build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<String?, String?>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<String?, String?>,
              String?,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
