import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/DTOs/user_profile.dart';
import 'package:vigia_ui/domain/profile_initials.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class AccountProfileCard extends StatelessWidget {
  const AccountProfileCard({
    super.key,
    required this.profile,
    required this.onChangePicture,
    required this.onRemovePicture,
    this.saving = false,
  });

  final UserProfile profile;
  final VoidCallback onChangePicture;
  final VoidCallback onRemovePicture;
  final bool saving;

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final picture = profile.pictureUrl;
    final initials = profileInitials(profile.name, profile.email);

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ClipOval(
                child: ColoredBox(
                  color: colorScheme.primaryContainer,
                  child: SizedBox(
                    width: 56,
                    height: 56,
                    child: picture != null && picture.isNotEmpty
                        ? Image.network(
                            picture,
                            fit: BoxFit.cover,
                            errorBuilder: (_, _, _) => _initials(theme, initials),
                          )
                        : _initials(theme, initials),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      profile.name,
                      style: theme.textTheme.titleMedium,
                      key: const Key('profile-name'),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      profile.email,
                      key: const Key('profile-email'),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            t.profilePhone,
            style: theme.textTheme.labelMedium?.copyWith(
              color: colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            profile.phone.isEmpty ? '—' : profile.phone,
            key: const Key('profile-phone'),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              TextButton(
                onPressed: saving ? null : onChangePicture,
                child: Text(t.changeProfilePicture),
              ),
              if (picture != null && picture.isNotEmpty)
                TextButton(
                  onPressed: saving ? null : onRemovePicture,
                  child: Text(t.removeProfilePicture),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _initials(ThemeData theme, String initials) {
    if (initials.isEmpty) {
      return Icon(Icons.person_rounded, color: theme.colorScheme.primary);
    }

    return Center(
      child: Text(
        initials,
        style: theme.textTheme.titleMedium?.copyWith(
          color: theme.colorScheme.primary,
        ),
      ),
    );
  }
}
