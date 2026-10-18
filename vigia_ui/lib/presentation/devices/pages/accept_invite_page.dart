import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/device_details_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/pending_invite_provider.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';

class AcceptInvitePage extends ConsumerStatefulWidget {
  const AcceptInvitePage({super.key, required this.token});

  final String token;

  @override
  ConsumerState<AcceptInvitePage> createState() => _AcceptInvitePageState();
}

class _AcceptInvitePageState extends ConsumerState<AcceptInvitePage> {
  bool _busy = false;
  bool _failed = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _accept());
  }

  Future<void> _accept() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _failed = false;
      _errorMessage = null;
    });

    final t = context.translations;

    try {
      await ref
          .read(deviceShareActionsProvider.notifier)
          .acceptInvite(widget.token);
      ref.read(pendingInviteTokenProvider.notifier).clear();
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(t.inviteAcceptedSuccess)));
      context.go(AppRoutes.devicesPage);
    } on RequestException catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _failed = true;
        _errorMessage = _messageFor(t, e.errorCode);
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _failed = true;
        _errorMessage = t.inviteAcceptedError;
      });
    }
  }

  String _messageFor(AppLocalizations t, ErrorCodes? code) {
    return switch (code) {
      ErrorCodes.inviteExpired => t.inviteExpired,
      ErrorCodes.inviteInvalid => t.inviteInvalid,
      ErrorCodes.groupUserLimitReached => t.inviteGroupFull,
      _ => t.inviteAcceptedError,
    };
  }

  @override
  Widget build(BuildContext context) {
    final t = context.translations;

    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_failed) ...[
              Text(_errorMessage ?? t.inviteAcceptedError),
              const SizedBox(height: 16),
              FilledButton(onPressed: _accept, child: Text(t.inviteRetry)),
            ] else ...[
              const AppLoadingIndicator(),
              const SizedBox(height: 16),
              Text(t.acceptingInvite),
            ],
          ],
        ),
      ),
    );
  }
}
