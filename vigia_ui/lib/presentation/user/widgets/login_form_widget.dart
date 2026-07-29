import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/domain/enums/auth_status.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_provider.dart';

class LoginForm extends ConsumerStatefulWidget {
  const LoginForm({super.key});

  @override
  ConsumerState<ConsumerStatefulWidget> createState() => _LoginFormState();
}

class _LoginFormState extends ConsumerState<LoginForm> {
  bool _isPasswordVisible = true;

  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _emailController.addListener(_onFieldsChanged);
    _passwordController.addListener(_onFieldsChanged);
  }

  @override
  void dispose() {
    _emailController
      ..removeListener(_onFieldsChanged)
      ..dispose();
    _passwordController
      ..removeListener(_onFieldsChanged)
      ..dispose();
    super.dispose();
  }

  void _onFieldsChanged() => setState(() {});

  bool get _canSubmit =>
      _emailController.text.isNotEmpty && _passwordController.text.isNotEmpty;

  Future<void> _submit() async {
    if (ref.read(authControllerProvider).isLoading) return;

    ref.read(authExitTransitionProvider.notifier).armLogin();

    await ref
        .read(authControllerProvider.notifier)
        .login(_emailController.text, _passwordController.text);

    if (!mounted) return;

    final status = ref.read(authControllerProvider).status;

    switch (status) {
      case AuthStatus.unauthorized:
        ref.read(authExitTransitionProvider.notifier).disarm();
        _showSnackBar(
          context,
          context.translations.invalidCredentials,
          Theme.of(context).colorScheme.error,
        );
        break;
      case AuthStatus.error:
        ref.read(authExitTransitionProvider.notifier).disarm();
        _showSnackBar(
          context,
          context.translations.loginError,
          Theme.of(context).colorScheme.error,
        );
        break;
      case AuthStatus.authorized:
        // Navigation is handled by GoRouter redirect + auth exit transition.
        break;
      default:
        ref.read(authExitTransitionProvider.notifier).disarm();
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      children: [
        _buildTextField(
          _emailController,
          context.translations.email,
          Icons.email_outlined,
        ),
        Padding(
          padding: const EdgeInsetsGeometry.symmetric(vertical: 16),
          child: _buildTextField(
            _passwordController,
            context.translations.password,
            Icons.lock_outline,
            isPassword: true,
          ),
        ),
        TweenAnimationBuilder<double>(
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeInOut,
          tween: Tween<double>(end: _canSubmit ? 1.0 : 0.0),
          builder: (context, t, child) {
            final background = Color.lerp(
              colorScheme.surface,
              colorScheme.secondary,
              t,
            )!;
            final foreground = Color.lerp(
              colorScheme.onSurface.withValues(alpha: 0.38),
              colorScheme.onSecondary,
              t,
            )!;

            return ElevatedButton(
              onPressed: _canSubmit ? _submit : null,
              style: ButtonStyle(
                maximumSize: WidgetStateProperty.all(
                  const Size(double.infinity, 50),
                ),
                minimumSize: WidgetStateProperty.all(
                  const Size(double.infinity, 50),
                ),
                padding: WidgetStateProperty.all(EdgeInsets.zero),
                shape: WidgetStateProperty.all(
                  RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                // Same color for all states so Material does not snap on disable.
                backgroundColor: WidgetStateProperty.all(background),
                foregroundColor: WidgetStateProperty.all(foreground),
              ),
              child: child,
            );
          },
          child: Wrap(
            spacing: 8,
            alignment: WrapAlignment.center,
            runAlignment: WrapAlignment.center,
            runSpacing: 8,
            children: [
              ref.watch(authControllerProvider).isLoading
                  ? const CircularProgressIndicator.adaptive()
                  : const Icon(Icons.login_rounded, size: 20),
              Text(context.translations.login, style: TextStyle(fontSize: 16)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTextField(
    TextEditingController controller,
    String label,
    IconData icon, {
    bool isPassword = false,
  }) {
    final colorScheme = Theme.of(context).colorScheme;
    const borderRadius = BorderRadius.all(Radius.circular(10));

    // Matches AuthPage scaffold (primary) so the outline disappears at rest.
    final hiddenBorder = OutlineInputBorder(
      borderRadius: borderRadius,
      borderSide: BorderSide(color: colorScheme.surface),
    );
    final focusedBorder = OutlineInputBorder(
      borderRadius: borderRadius,
      borderSide: BorderSide(color: colorScheme.surface, width: 2),
    );

    return TextField(
      controller: controller,
      obscureText: isPassword && _isPasswordVisible,
      cursorColor: colorScheme.onPrimary,
      decoration: InputDecoration(
        filled: true,
        fillColor: colorScheme.surface,
        prefixIcon: Icon(icon, color: colorScheme.onSurfaceVariant),
        labelText: label,
        labelStyle: TextStyle(color: colorScheme.onSurfaceVariant),
        floatingLabelBehavior: FloatingLabelBehavior.auto,
        floatingLabelStyle: TextStyle(
          color: colorScheme.onSurface,
          fontWeight: FontWeight.w500,
        ),
        border: hiddenBorder,
        enabledBorder: hiddenBorder,
        focusedBorder: focusedBorder,
        suffixIcon: isPassword
            ? IconButton(
                style: const ButtonStyle(splashFactory: NoSplash.splashFactory),
                onPressed: () {
                  _isPasswordVisible = !_isPasswordVisible;
                  setState(() {});
                },
                icon: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  transitionBuilder: (child, animation) =>
                      ScaleTransition(scale: animation, child: child),
                  child: _isPasswordVisible
                      ? const Icon(
                          key: ValueKey(1),
                          Icons.visibility_off_outlined,
                        )
                      : const Icon(key: ValueKey(2), Icons.visibility_outlined),
                ),
              )
            : null,
      ),
    );
  }

  void _showSnackBar(BuildContext context, String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
        behavior: SnackBarBehavior.fixed,
        duration: const Duration(seconds: 2),
      ),
    );
  }
}
