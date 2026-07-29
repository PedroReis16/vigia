import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:rxdart/rxdart.dart';
import 'package:vigia_ui/domain/enums/auth_status.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shared/extensions/text_editing_controller_stream.dart';
import 'package:vigia_ui/presentation/shared/widgets/form_text_field.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_provider.dart';

class LoginForm extends ConsumerStatefulWidget {
  const LoginForm({super.key});

  @override
  ConsumerState<ConsumerStatefulWidget> createState() => _LoginFormState();
}

class _LoginFormState extends ConsumerState<LoginForm> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  late final StreamSubscription<bool> _validationSub;
  bool _canSubmit = false;

  @override
  void initState() {
    super.initState();

    _validationSub =
        Rx.combineLatest2(
              _emailController.toStream(),
              _passwordController.toStream(),
              (email, password) => email.isNotEmpty && password.isNotEmpty,
            )
            .debounceTime(const Duration(milliseconds: 400))
            .distinct()
            .listen((canSubmit) {
              if (!mounted) return;
              setState(() => _canSubmit = canSubmit);
            });
  }

  @override
  void dispose() {
    _validationSub.cancel();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

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
        FormTextField(
          label: context.translations.email,
          icon: Icons.email_outlined,
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
        ),
        Padding(
          padding: const EdgeInsetsGeometry.symmetric(vertical: 16),
          child: FormTextField(
            label: context.translations.password,
            icon: Icons.lock_outline,
            controller: _passwordController,
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
