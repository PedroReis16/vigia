import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/device_details_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/pending_invite_provider.dart';

class AcceptInvitePage extends ConsumerStatefulWidget {
  const AcceptInvitePage({super.key, required this.token});

  final String token;

  @override
  ConsumerState<AcceptInvitePage> createState() => _AcceptInvitePageState();
}

class _AcceptInvitePageState extends ConsumerState<AcceptInvitePage> {
  bool _started = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _accept());
  }

  Future<void> _accept() async {
    if (_started) return;
    _started = true;

    final t = context.translations;

    try {
      await ref
          .read(deviceShareActionsProvider.notifier)
          .acceptInvite(widget.token);
      ref.read(pendingInviteTokenProvider.notifier).clear();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t.inviteAcceptedSuccess)),
      );
      context.go(AppRoutes.devicesPage);
    } catch (e) {
      ref.read(pendingInviteTokenProvider.notifier).clear();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t.inviteAcceptedError)),
      );
      context.go(AppRoutes.devicesPage);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = context.translations;

    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(t.acceptingInvite),
          ],
        ),
      ),
    );
  }
}
