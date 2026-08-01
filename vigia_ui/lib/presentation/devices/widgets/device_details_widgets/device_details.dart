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

class _DeviceDetailsState extends ConsumerState<DeviceDetails> {
  int _currentPage = 0;

  final EdgeInsetsGeometry _padding = const EdgeInsets.fromLTRB(16, 16, 16, 24);

  late final PageController _pageController;

  late List<UserUIModel> _users;

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: _currentPage);
    _users = [];
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _returnToDeviceDetails() {
    _currentPage = 0;
    _transitionAnimation(_currentPage);
    setState(() {});
  }

  void _routeToEditDeviceProperties() {
    _currentPage = 1;
    _transitionAnimation(_currentPage);
    setState(() {});
  }

  void _routeToDeviceUsers() {
    _currentPage = 2;
    _transitionAnimation(_currentPage);
    setState(() {});
  }

  void _transitionAnimation(int page) => _pageController.animateToPage(
    page,
    duration: const Duration(milliseconds: 300),
    curve: Curves.easeInOut,
  );

  @override
  Widget build(BuildContext context) {
    return PageView(
      controller: _pageController,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        _buildBasePage(context),
        EditDeviceProperties(
          device: widget.device,
          returnToPreviousPage: _returnToDeviceDetails,
        ),
        DeviceUsers(
          users: _users,
          returnToPreviousPage: _returnToDeviceDetails,
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

        Text("Usuários"),
        const SizedBox(height: 8),
        SingleChildScrollView(
          child: ref
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
                    return Text("Nenhum usuário encontrado");
                  }

                  _users = users;

                  // bool hasManyUsers = users.length > 1;
                  bool hasManyUsers = true;

                  return GestureDetector(
                    onTap: hasManyUsers ? () => _routeToDeviceUsers() : null,
                    child: hasManyUsers
                        ? DeviceUserItem(
                            user: users.first,
                            showActionIcon: false,
                          )
                        : Column(
                            children: [
                              ...users
                                  .map(
                                    (user) => DeviceUserItem(
                                      user: user,
                                      showActionIcon: user.isOwner,
                                    ),
                                  )
                                  .take(3),
                            ],
                          ),
                  );
                },
              ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Text("Clips"),
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
          child: Text("Ver Clips", textAlign: TextAlign.start),
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
