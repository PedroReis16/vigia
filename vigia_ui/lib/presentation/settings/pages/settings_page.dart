import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/settings/widgets/settings_section.dart';
import 'package:vigia_ui/presentation/settings/widgets/settings_tile.dart';
import 'package:vigia_ui/presentation/shell/auth_transition_warm_up.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  static const _padding = EdgeInsets.fromLTRB(16, 16, 16, 24);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = context.translations;
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      body: ListView(
        padding: _padding,
        children: [
          Text(t.settings, style: theme.textTheme.headlineSmall),
          const SizedBox(height: 24),
          SettingsSection(
            title: t.account,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 14,
                ),
                child: Row(
                  children: [
                    ClipOval(
                      child: ColoredBox(
                        color: colorScheme.primaryContainer,
                        child: SizedBox(
                          width: 48,
                          height: 48,
                          child: Icon(
                            Icons.person_rounded,
                            color: colorScheme.primary,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        t.account,
                        style: theme.textTheme.titleMedium,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          SettingsSection(
            title: t.session,
            children: [
              SettingsTile(
                icon: Icons.logout_rounded,
                title: t.logout,
                iconColor: colorScheme.error,
                titleColor: colorScheme.error,
                trailing: const SizedBox.shrink(),
                onTap: () => _signOut(context, ref),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _signOut(BuildContext context, WidgetRef ref) async {
    await AuthTransitionWarmUp.precacheLogos(context);
    if (!context.mounted) return;
    ref.read(authExitTransitionProvider.notifier).armLogout();
    ref.read(authSessionProvider.notifier).signOut();
  }
}
