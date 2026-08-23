import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:rxdart/rxdart.dart';
import 'package:vigia_ui/domain/enums/auth_status.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shared/extensions/show_snackbar.dart';
import 'package:vigia_ui/presentation/shared/extensions/text_editing_controller_stream.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';
import 'package:vigia_ui/presentation/shared/widgets/form_text_field.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_provider.dart';

class LoginForm extends ConsumerStatefulWidget {
  const LoginForm({super.key});

  @override
  ConsumerState<ConsumerStatefulWidget> createState() => _LoginFormState();
}

class _LoginFormState extends ConsumerState<LoginForm> {
  static const _welcomeHold = Duration(milliseconds: 1600);

  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  late final StreamSubscription<bool> _validationSub;
  bool _canSubmit = false;
  bool _busy = false;
  bool _showWelcome = false;

  @override
  void initState() {
    super.initState();

    _validationSub =
        Rx.combineLatest2(
          _emailController.toStream(),
          _passwordController.toStream(),
          (email, password) => email.isNotEmpty && password.isNotEmpty,
        ).debounceTime(const Duration(milliseconds: 400)).distinct().listen((
          canSubmit,
        ) {
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
    if (_busy || ref.read(authControllerProvider).isLoading) return;

    FocusScope.of(context).unfocus();
    setState(() => _busy = true);

    final credentials = await ref
        .read(authControllerProvider.notifier)
        .login(_emailController.text, _passwordController.text);

    if (!mounted) return;

    final status = ref.read(authControllerProvider).status;

    if (status != AuthStatus.authorized || credentials == null) {
      setState(() => _busy = false);

      switch (status) {
        case AuthStatus.unauthorized:
          context.showSnackbar(
            message: context.translations.invalidCredentials,
            color: Theme.of(context).colorScheme.error,
          );
        case AuthStatus.error:
          context.showSnackbar(
            message: context.translations.loginError,
            color: Theme.of(context).colorScheme.error,
          );
        default:
          break;
      }
      return;
    }

    setState(() => _showWelcome = true);

    await Future.delayed(_welcomeHold);
    if (!mounted) return;

    ref.read(authExitTransitionProvider.notifier).armLogin();
    await ref.read(authControllerProvider.notifier).commitSession(credentials);
  }

  Widget _buildButtonLabel({required bool isLoading}) {
    final Widget child;
    final String key;
    final showLoading = (isLoading || _busy) && !_showWelcome;

    if (_showWelcome) {
      key = 'welcome';
      child = Text(
        context.translations.welcomeToVigia,
        style: const TextStyle(fontSize: 16),
        textAlign: TextAlign.center,
      );
    } else {
      key = showLoading ? 'loading' : 'idle';
      child = Wrap(
        spacing: 8,
        alignment: WrapAlignment.center,
        runAlignment: WrapAlignment.center,
        runSpacing: 8,
        children: [
          showLoading
              ? AppLoadingIndicator(
                  size: 20,
                  strokeWidth: 2,
                  color: Theme.of(context).colorScheme.onPrimary,
                )
              : const Icon(Icons.login_rounded, size: 20),
          Text(context.translations.login, style: const TextStyle(fontSize: 16)),
        ],
      );
    }

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 320),
      switchInCurve: Curves.easeOutCubic,
      switchOutCurve: Curves.easeInCubic,
      transitionBuilder: (child, animation) {
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.15),
              end: Offset.zero,
            ).animate(animation),
            child: child,
          ),
        );
      },
      child: KeyedSubtree(key: ValueKey(key), child: child),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isLoading = ref.watch(authControllerProvider).isLoading;
    final buttonActive = _canSubmit || _showWelcome;

    return Column(
      children: [
        FormTextField(
          label: context.translations.email,
          icon: Icons.email_outlined,
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
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
          tween: Tween<double>(end: buttonActive ? 1.0 : 0.0),
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

            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 48),
              child: ElevatedButton(
                onPressed: (_canSubmit && !_busy) ? _submit : null,
                style: ButtonStyle(
                  maximumSize: WidgetStateProperty.all(
                    const Size(double.infinity, 50),
                  ),
                  minimumSize: WidgetStateProperty.all(
                    const Size(double.infinity, 50),
                  ),
                  padding: WidgetStateProperty.all(
                    const EdgeInsets.symmetric(horizontal: 16),
                  ),
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
              ),
            );
          },
          child: _buildButtonLabel(isLoading: isLoading),
        ),
      ],
    );
  }
}
