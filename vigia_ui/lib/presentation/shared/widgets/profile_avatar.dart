import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/profile_initials.dart';

class ProfileAvatar extends StatelessWidget {
  const ProfileAvatar({
    super.key,
    required this.name,
    required this.email,
    this.pictureUrl,
    this.size = 56,
    this.borderColor,
    this.borderWidth = 0,
  });

  final String name;
  final String email;
  final String? pictureUrl;
  final double size;
  final Color? borderColor;
  final double borderWidth;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final initials = profileInitials(name, email);
    final picture = pictureUrl;

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: borderWidth > 0
            ? Border.all(
                color: borderColor ?? theme.colorScheme.primary,
                width: borderWidth,
              )
            : null,
      ),
      child: ClipOval(
        child: picture != null && picture.isNotEmpty
            ? Image.network(
                picture,
                width: size,
                height: size,
                fit: BoxFit.cover,
                errorBuilder: (_, _, _) => _fallback(theme, initials),
              )
            : _fallback(theme, initials),
      ),
    );
  }

  Widget _fallback(ThemeData theme, String initials) {
    return ColoredBox(
      color: theme.colorScheme.primaryContainer,
      child: Center(
        child: initials.isEmpty
            ? Icon(
                Icons.person_rounded,
                color: theme.colorScheme.primary,
                size: size * 0.5,
              )
            : Text(
                initials,
                style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.primary,
                  fontSize: size * 0.32,
                ),
              ),
      ),
    );
  }
}
