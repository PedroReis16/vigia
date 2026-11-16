import 'package:vigia_ui/domain/environments.dart';

/// Turns an API-relative asset path into an absolute URL for image widgets.
String? resolveApiAssetUrl(String? path) {
  final trimmed = path?.trim();
  if (trimmed == null || trimmed.isEmpty) return null;
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed;
  }

  final base = Environments.apiUrl.replaceAll(RegExp(r'/+$'), '');
  if (base.isEmpty) return trimmed;

  final relative = trimmed.replaceFirst(RegExp(r'^/+'), '');
  return '$base/$relative';
}
