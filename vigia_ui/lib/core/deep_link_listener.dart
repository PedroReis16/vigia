import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/core/app_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/core/invite_deep_link.dart';
import 'package:vigia_ui/presentation/devices/providers/pending_invite_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

/// Listens for `vigia://invite/{token}` deep links and routes accordingly.
///
/// GoRouter platform deep linking is disabled (`overridePlatformDefaultLocation`)
/// because custom schemes like `vigia://...` do not match in-app paths and
/// would otherwise surface PageNotFound.
class DeepLinkListener extends ConsumerStatefulWidget {
  const DeepLinkListener({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<DeepLinkListener> createState() => _DeepLinkListenerState();
}

class _DeepLinkListenerState extends ConsumerState<DeepLinkListener> {
  StreamSubscription<Uri>? _sub;
  final AppLinks _appLinks = AppLinks();

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    try {
      final initial = await _appLinks.getInitialLink();
      if (initial != null) {
        _handleUri(initial);
      }
    } catch (_) {}

    _sub = _appLinks.uriLinkStream.listen(_handleUri);
  }

  void _handleUri(Uri uri) {
    final token = InviteDeepLink.extractToken(uri);
    if (token == null || token.isEmpty) return;

    ref.read(pendingInviteTokenProvider.notifier).setToken(token);

    final loggedIn = ref.read(authSessionProvider).asData?.value ?? false;
    final router = ref.read(appRouterProvider);

    // Defer until after the current frame so GoRouter has finished bootstrapping.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (loggedIn) {
        router.go(AppRoutes.invitePagePath(token));
      } else {
        router.go(AppRoutes.authPage);
      }
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
