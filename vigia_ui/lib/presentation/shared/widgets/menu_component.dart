import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/settings/providers/user_profile_provider.dart';
import 'package:vigia_ui/presentation/shared/widgets/profile_avatar.dart';

class MenuComponent extends ConsumerWidget {
  final int currentIndex;
  final ValueChanged<int> onItemTap;

  const MenuComponent({
    super.key,
    required this.currentIndex,
    required this.onItemTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          IconButton(
            onPressed: () {
              if (!ref.watch(devicesProvider).isLoading && currentIndex == 0) {
                ref.read(devicesProvider.notifier).refresh();
                return;
              }

              onItemTap(0);
            },
            icon: Icon(
              Icons.dashboard_rounded,
              color: currentIndex == 0
                  ? colorScheme.primary
                  : colorScheme.onSurface.withValues(alpha: 0.4),
            ),
          ),
          IconButton(
            tooltip: context.translations.profileTitle,
            onPressed: () => onItemTap(1),
            icon: _profileAvatar(ref, colorScheme, currentIndex == 1),
          ),
        ],
      ),
    );
  }

  Widget _profileAvatar(WidgetRef ref, ColorScheme colorScheme, bool selected) {
    final profile = ref.watch(userProfileProvider).asData?.value;
    return Opacity(
      opacity: selected ? 1 : 0.45,
      child: ProfileAvatar(
        key: const Key('nav-profile-avatar'),
        name: profile?.name ?? '',
        email: profile?.email ?? '',
        pictureUrl: profile?.pictureUrl,
        size: 32,
        borderWidth: 2,
        borderColor: selected ? colorScheme.primary : Colors.transparent,
      ),
    );
  }
}
