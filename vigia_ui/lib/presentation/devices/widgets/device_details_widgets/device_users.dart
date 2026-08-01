import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_user_item.dart';

class DeviceUsers extends ConsumerWidget {
  final List<UserUIModel> users;
  final VoidCallback returnToPreviousPage;

  const DeviceUsers({
    super.key,
    required this.users,
    required this.returnToPreviousPage,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            runSpacing: 8,
            alignment: WrapAlignment.start,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              IconButton(
                onPressed: returnToPreviousPage,
                icon: Icon(Icons.arrow_back),
              ),
              Text("Voltar"),
            ],
          ),
          Text("Usuários"),
          const SizedBox(height: 8),
          ...users.map(
            (user) => DeviceUserItem(user: user, showActionIcon: user.isOwner),
          ),
        ],
      ),
    );
  }
}
