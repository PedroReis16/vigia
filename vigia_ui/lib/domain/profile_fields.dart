final _phonePattern = RegExp(r'^[0-9+() .-]{8,16}$');

bool isValidProfileName(String value) {
  final name = value.trim();
  if (name.isEmpty || name.length > 64) return false;
  if (name.contains('<') || name.contains('>')) return false;
  for (final rune in name.runes) {
    if (rune < 32 || rune == 127) return false;
  }
  return true;
}

bool isValidProfilePhone(String value) {
  return _phonePattern.hasMatch(value.trim());
}
