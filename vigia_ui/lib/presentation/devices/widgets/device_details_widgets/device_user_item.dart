import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';

class DeviceUserItem extends StatelessWidget {
  final UserUIModel user;
  final bool showActionIcon;
  final VoidCallback? onActionIconPressed;

  const DeviceUserItem({
    super.key,
    required this.user,
    this.showActionIcon = false,
    this.onActionIconPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          spacing: 8,
          children: [
            ClipOval(
              child: SizedBox(
                width: 40,
                height: 40,
                child: user.userPicture != null
                    ? Image.network(
                        user.userPicture!,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => ColoredBox(
                          color: Colors.grey.shade300,
                          child: const Icon(Icons.person),
                        ),
                      )
                    : ColoredBox(
                        color: Colors.grey.shade300,
                        child: const Icon(Icons.person),
                      ),
              ),
            ),
            Text(user.name),
          ],
        ),
        if (user.isOwner && showActionIcon)
          Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey.shade500),
      ],
    );
  }
}
