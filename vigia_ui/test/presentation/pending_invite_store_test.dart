import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/presentation/devices/providers/pending_invite_provider.dart';

void main() {
  test('pending token is restored from the store', () async {
    final store = MemoryPendingInviteStore();
    pendingInviteStoreOverride = store;
    addTearDown(() => pendingInviteStoreOverride = null);

    final first = ProviderContainer();
    addTearDown(first.dispose);
    first.read(pendingInviteTokenProvider.notifier).setToken('abc');
    await pumpEventQueue();
    expect(store.value, 'abc');

    final second = ProviderContainer();
    addTearDown(second.dispose);
    second.read(pendingInviteTokenProvider);
    await pumpEventQueue();

    expect(second.read(pendingInviteTokenProvider), 'abc');
  });
}
