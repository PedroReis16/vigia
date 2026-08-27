import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/core/theme/app_assets.dart';
import 'package:vigia_ui/data/services/token_storage_service.dart';
import 'package:vigia_ui/domain/constants.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/device_details_provider.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_user_item.dart';
import 'package:vigia_ui/presentation/shared/extensions/show_snackbar.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';

class DeviceUsers extends ConsumerStatefulWidget {
  final String deviceId;
  final bool isOwner;
  final List<UserUIModel> users;
  final VoidCallback returnToPreviousPage;

  const DeviceUsers({
    super.key,
    required this.deviceId,
    required this.isOwner,
    required this.users,
    required this.returnToPreviousPage,
  });

  @override
  ConsumerState<DeviceUsers> createState() => _DeviceUsersState();
}

class _DeviceUsersState extends ConsumerState<DeviceUsers> {
  String? _currentUserId;
  bool _sharing = false;

  @override
  void initState() {
    super.initState();
    TokenStorageService().getUserId().then((id) {
      if (mounted) setState(() => _currentUserId = id);
    });
  }

  Future<void> _shareInvite() async {
    if (_sharing) return;
    setState(() => _sharing = true);
    final t = context.translations;
    final theme = Theme.of(context);

    try {
      final invite = await ref
          .read(deviceShareActionsProvider.notifier)
          .generateShareLink(widget.deviceId);

      await Clipboard.setData(ClipboardData(text: invite.inviteUrl));

      if (!mounted) return;

      // Share sheet often fails on emulators / iOS without a valid origin.
      // Clipboard already has the link, so treat share failures as non-fatal.
      try {
        final box = context.findRenderObject() as RenderBox?;
        final origin = box != null
            ? box.localToGlobal(Offset.zero) & box.size
            : const Rect.fromLTWH(0, 0, 1, 1);

        final iconFile = await _prepareShareIcon();
        if (iconFile != null) {
          await Share.shareXFiles(
            [XFile(iconFile.path, mimeType: 'image/png', name: 'vigia.png')],
            text: invite.inviteUrl,
            subject: t.shareDeviceInviteSubject,
            sharePositionOrigin: origin,
          );
        } else {
          await Share.share(
            invite.inviteUrl,
            subject: t.shareDeviceInviteSubject,
            sharePositionOrigin: origin,
          );
        }
      } catch (_) {}

      if (!mounted) return;
      context.showSnackbar(
        message: t.shareLinkCopied,
        color: theme.colorScheme.onSurface,
      );
    } catch (e) {
      if (!mounted) return;
      context.showSnackbar(
        message: t.shareLinkError,
        color: theme.colorScheme.error,
      );
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  Future<File?> _prepareShareIcon() async {
    try {
      final bytes = await rootBundle.load(AppAssets.icon);
      final file = File('${Directory.systemTemp.path}/vigia_share_icon.png');
      await file.writeAsBytes(bytes.buffer.asUint8List());
      return file;
    } catch (_) {
      return null;
    }
  }

  Future<void> _confirmRemove(UserUIModel user) async {
    final t = context.translations;
    final isSelf = user.id == _currentUserId;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isSelf ? t.leaveGroupTitle : t.removeUserTitle),
        content: Text(
          isSelf ? t.leaveGroupMessage : t.removeUserMessage(user.name),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(t.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(isSelf ? t.leaveGroupConfirm : t.removeUserConfirm),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    final theme = Theme.of(context);
    try {
      await ref
          .read(deviceShareActionsProvider.notifier)
          .removeUser(widget.deviceId, user.id);

      if (!mounted) return;

      if (isSelf) {
        context.showSnackbar(
          message: t.leftGroupSuccess,
          color: theme.colorScheme.onSurface,
        );
        if (context.mounted) {
          context.go(AppRoutes.devicesPage);
        }
        return;
      }

      context.showSnackbar(
        message: t.userRemovedSuccess,
        color: theme.colorScheme.onSurface,
      );
    } catch (_) {
      if (!mounted) return;
      context.showSnackbar(
        message: t.userRemoveError,
        color: theme.colorScheme.error,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);
    final usersAsync = ref.watch(getDeviceUsersProvider(widget.deviceId));
    final users = usersAsync.asData?.value ?? widget.users;
    final atLimit = users.length >= Constants.maxGroupUsers;
    final canShare = widget.isOwner && !atLimit;

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Wrap(
                runSpacing: 8,
                alignment: WrapAlignment.start,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  IconButton(
                    onPressed: widget.returnToPreviousPage,
                    icon: const Icon(Icons.arrow_back_ios),
                  ),
                  Text(t.deviceUsers, style: theme.textTheme.titleLarge),
                ],
              ),
              Text(
                t.deviceUsersCount(users.length, Constants.maxGroupUsers),
                style: theme.textTheme.labelLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          Expanded(
            child: usersAsync.when(
              loading: () => const Center(child: AppLoadingIndicator()),
              error: (e, _) => Center(child: Text(e.toString())),
              data: (list) {
                if (list.isEmpty) {
                  return Center(child: Text(t.noUsersFound));
                }
                return ListView.separated(
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final user = list[index];
                    final isSelf = user.id == _currentUserId;
                    final canRemove =
                        !user.isOwner && (widget.isOwner || isSelf);

                    return DeviceUserItem(
                      user: user,
                      showActionIcon: canRemove,
                      actionIcon: isSelf ? Icons.logout : Icons.person_remove,
                      onActionIconPressed: canRemove
                          ? () => _confirmRemove(user)
                          : null,
                    );
                  },
                );
              },
            ),
          ),
          if (widget.isOwner)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: canShare && !_sharing ? _shareInvite : null,
                  icon: _sharing
                      ? AppLoadingIndicator(
                          size: 16,
                          strokeWidth: 2,
                          color: theme.colorScheme.onPrimary,
                        )
                      : const Icon(Icons.share),
                  label: Text(atLimit ? t.shareLimitReached : t.shareDevice),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
