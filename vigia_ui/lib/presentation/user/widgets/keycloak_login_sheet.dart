import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/data/services/keycloak_authorize.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';
import 'package:vigia_ui/domain/environments.dart';
import 'package:vigia_ui/presentation/user/providers/auth_provider.dart';
import 'package:webview_flutter/webview_flutter.dart';

sealed class KeycloakLoginOutcome {
  const KeycloakLoginOutcome();
}

class KeycloakLoginSuccess extends KeycloakLoginOutcome {
  const KeycloakLoginSuccess(this.credentials);

  final UserCredentials credentials;
}

class KeycloakLoginFailure extends KeycloakLoginOutcome {
  const KeycloakLoginFailure();
}

/// Keycloak login, registration and password reset inside the bottom sheet.
class KeycloakLoginSheet extends ConsumerStatefulWidget {
  const KeycloakLoginSheet({super.key});

  @override
  ConsumerState<KeycloakLoginSheet> createState() => _KeycloakLoginSheetState();
}

class _KeycloakLoginSheetState extends ConsumerState<KeycloakLoginSheet> {
  late final WebViewController _controller;
  late final String _verifier;
  late final String _state;

  bool _loadingPage = true;
  bool _exchanging = false;
  bool _handled = false;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _verifier = Pkce.verifier();
    _state = Pkce.verifier();
    final authorizeUri = KeycloakAuthorize.build(
      baseUrl: Environments.keycloakUrl,
      realm: Environments.keycloakRealm,
      clientId: Environments.keycloakClientId,
      codeChallenge: Pkce.challengeFor(_verifier),
      state: _state,
    );
    debugPrint('[Keycloak] authorize $authorizeUri');

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFFFFFFFF))
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (request) {
            if (_intercept(request.url)) {
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
          onUrlChange: (change) {
            final url = change.url;
            if (url != null) _intercept(url);
          },
          onPageFinished: (_) {
            if (mounted) {
              setState(() {
                _loadingPage = false;
                _loadError = null;
              });
            }
          },
          onWebResourceError: (error) {
            debugPrint(
              '[Keycloak] ${error.errorCode} ${error.description} ${error.url}',
            );
            if (!mounted || error.isForMainFrame == false) return;
            setState(() {
              _loadingPage = false;
              _loadError = error.description;
            });
          },
        ),
      );

    // The sheet's platform view has no size until the first frame.
    // Loading before that leaves a blank WKWebView on iOS.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _controller.loadRequest(authorizeUri);
    });
  }

  bool _intercept(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null || !KeycloakCallback.isCallback(uri)) return false;
    _handleCallback(uri);
    return true;
  }

  Future<void> _handleCallback(Uri uri) async {
    if (_handled) return;
    _handled = true;

    final callback = KeycloakCallback.tryParse(uri);
    if (callback == null ||
        callback.state != _state ||
        !callback.isSuccess ||
        callback.code == null) {
      _close(const KeycloakLoginFailure());
      return;
    }

    setState(() => _exchanging = true);
    final credentials = await ref
        .read(authControllerProvider.notifier)
        .completeLogin(code: callback.code!, codeVerifier: _verifier);
    if (!mounted) return;
    if (credentials == null) {
      _close(const KeycloakLoginFailure());
      return;
    }
    _close(KeycloakLoginSuccess(credentials));
  }

  void _close(KeycloakLoginOutcome outcome) {
    if (!mounted) return;
    Navigator.of(context).pop(outcome);
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        WebViewWidget(controller: _controller),
        if (_loadError != null)
          Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                _loadError!,
                textAlign: TextAlign.center,
              ),
            ),
          ),
        if (_loadingPage || _exchanging)
          const Align(
            alignment: Alignment.topCenter,
            child: LinearProgressIndicator(minHeight: 2),
          ),
      ],
    );
  }
}
