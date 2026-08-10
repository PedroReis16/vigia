import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class DeviceUserItem extends StatelessWidget {
  final UserUIModel user;
  final bool showActionIcon;
  final IconData? actionIcon;
  final VoidCallback? onActionIconPressed;

  const DeviceUserItem({
    super.key,
    required this.user,
    this.showActionIcon = false,
    this.actionIcon,
    this.onActionIconPressed,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final t = context.translations;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Row(
            children: [
              ClipOval(
                child: SizedBox(
                  width: 40,
                  height: 40,
                  child: user.userPicture != null
                      ? Image.network(
                          user.userPicture!,
                          fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => ColoredBox(
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
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(user.name, overflow: TextOverflow.ellipsis),
                    if (user.isOwner)
                      Text(
                        t.deviceOwner,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (showActionIcon)
          IconButton(
            onPressed: onActionIconPressed,
            icon: Icon(
              actionIcon ?? Icons.arrow_forward_ios,
              size: actionIcon == null ? 16 : 22,
              color: Colors.grey.shade500,
            ),
          ),
      ],
    );
  }
}
