String profileInitials(String name, String email) {
  final trimmedName = name.trim();
  final trimmedEmail = email.trim();
  final parts = trimmedName.split(RegExp(r'\s+')).where((part) => part.isNotEmpty);
  final nameIsEmail = trimmedName.toLowerCase() == trimmedEmail.toLowerCase();
  final nameParts = parts.toList();

  if (!nameIsEmail && nameParts.length >= 2) {
    return '${nameParts[0][0]}${nameParts[1][0]}'.toUpperCase();
  }

  if (!nameIsEmail && nameParts.length == 1 && nameParts[0].isNotEmpty) {
    return nameParts[0][0].toUpperCase();
  }

  final local = trimmedEmail.split('@').first;
  if (local.length <= 2) return local.toUpperCase();
  return local.substring(0, 2).toUpperCase();
}
