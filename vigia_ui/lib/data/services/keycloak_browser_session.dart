import 'package:webview_flutter/webview_flutter.dart';

/// Clears the Keycloak cookies kept by the in-app login WebView.
class KeycloakBrowserSession {
  Future<void> clear() => WebViewCookieManager().clearCookies();
}
