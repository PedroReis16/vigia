import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:skeletonizer/skeletonizer.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/helpers/converters.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/device_details_provider.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_user_item.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_users.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/edit_device_properties.dart';

class DeviceDetails extends ConsumerStatefulWidget {
  const DeviceDetails({super.key, required this.device});

  final DeviceUIModel device;

  @override
  ConsumerState<DeviceDetails> createState() => _DeviceDetailsState();
}

enum _DeviceDetailsPane { details, edit, users }

class _DeviceDetailsState extends ConsumerState<DeviceDetails> {
  _DeviceDetailsPane _pane = _DeviceDetailsPane.details;

  final EdgeInsetsGeometry _padding = const EdgeInsets.fromLTRB(16, 16, 16, 24);

  late final PageController _pageController;

  late List<UserUIModel> _users;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _users = [];
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _returnToDeviceDetails() {
    _pageController
        .animateToPage(
          0,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        )
        .then((_) {
          if (!mounted) return;
          setState(() => _pane = _DeviceDetailsPane.details);
        });
  }

  void _routeToEditDeviceProperties() => _openPane(_DeviceDetailsPane.edit);

  void _routeToDeviceUsers() => _openPane(_DeviceDetailsPane.users);

  void _openPane(_DeviceDetailsPane pane) {
    setState(() => _pane = pane);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _pageController.animateToPage(
        1,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return PageView(
      controller: _pageController,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        KeyedSubtree(
          key: const ValueKey('device-details'),
          child: _buildBasePage(context),
        ),
        KeyedSubtree(
          key: ValueKey(_pane),
          child: switch (_pane) {
            _DeviceDetailsPane.edit => EditDeviceProperties(
              device: widget.device,
              returnToPreviousPage: _returnToDeviceDetails,
            ),
            _DeviceDetailsPane.users => DeviceUsers(
              deviceId: widget.device.id,
              isOwner: widget.device.isOwner,
              users: _users,
              returnToPreviousPage: _returnToDeviceDetails,
            ),
            _DeviceDetailsPane.details => const SizedBox.expand(),
          },
        ),
      ],
    );
  }

  Widget _buildBasePage(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);

    return ListView(
      padding: _padding,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              widget.device.nickname ?? widget.device.name,
              style: theme.textTheme.headlineSmall,
            ),
            if (widget.device.isOwner)
              IconButton(
                onPressed: () => _routeToEditDeviceProperties(),
                icon: const Icon(Icons.edit),
              ),
          ],
        ),
        const SizedBox(height: 16),
        _buildInfoTile(context, t.deviceNickname, widget.device.nickname ?? ""),
        if (widget.device.room != null)
          _buildInfoTile(
            context,
            t.deviceRoom,
            Converters.translateDeviceRoom(context, widget.device.room!),
          ),
        _buildInfoTile(context, t.deviceIdLabel, widget.device.id),

        Text(t.deviceUsers, style: theme.textTheme.titleMedium),
        const SizedBox(height: 8),
        ref
            .watch(getDeviceUsersProvider(widget.device.id))
            .when(
              error: (error, stackTrace) =>
                  Center(child: Text(error.toString())),
              loading: () => Skeletonizer(
                child: DeviceUserItem(
                  user: UserUIModel(id: "", name: "", isOwner: false),
                ),
              ),
              data: (users) {
                if (users.isEmpty) {
                  return Text(t.noUsersFound);
                }

                _users = users;

                final hasManyUsers = users.length > 3;
                final previewUsers = users.take(3).toList();

                return GestureDetector(
                  onTap: () => _routeToDeviceUsers(),
                  behavior: HitTestBehavior.opaque,
                  child: Column(
                    children: [
                      ...previewUsers.map(
                        (user) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: DeviceUserItem(
                            user: user,
                            showActionIcon:
                                hasManyUsers && user == previewUsers.last,
                            actionIcon: hasManyUsers
                                ? Icons.arrow_forward_ios
                                : null,
                          ),
                        ),
                      ),
                      if (hasManyUsers)
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            t.seeAllUsers,
                            style: theme.textTheme.labelLarge?.copyWith(
                              color: theme.colorScheme.primary,
                            ),
                          ),
                        ),
                    ],
                  ),
                );
              },
            ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Text(t.clips, style: theme.textTheme.titleMedium),
        ),
        TextButton(
          onPressed: () {
            context.push(
              AppRoutes.deviceClipsPage.replaceAll(
                ':deviceId',
                widget.device.id,
              ),
            );
          },
          child: Text(t.viewClips, textAlign: TextAlign.start),
        ),
      ],
    );
  }
}

Widget _buildInfoTile(BuildContext context, String label, String value) {
  final theme = Theme.of(context);
  return Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: theme.textTheme.labelMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 4),
        Text(value, style: theme.textTheme.bodyLarge),
      ],
    ),
  );
}
