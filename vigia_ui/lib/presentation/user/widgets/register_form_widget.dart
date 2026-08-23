import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';
import 'package:rxdart/rxdart.dart';
import 'package:vigia_ui/domain/enums/auth_status.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shared/extensions/show_snackbar.dart';
import 'package:vigia_ui/presentation/shared/extensions/text_editing_controller_stream.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';
import 'package:vigia_ui/presentation/shared/widgets/form_text_field.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_provider.dart';

enum _RegisterFieldError { none, email, password, passwordConfirm }

class _RegisterValidation {
  const _RegisterValidation({required this.canSubmit, required this.error});

  final bool canSubmit;
  final _RegisterFieldError error;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is _RegisterValidation &&
          canSubmit == other.canSubmit &&
          error == other.error;

  @override
  int get hashCode => Object.hash(canSubmit, error);
}

class RegisterForm extends ConsumerStatefulWidget {
  const RegisterForm({super.key});

  @override
  ConsumerState<ConsumerStatefulWidget> createState() => _RegisterFormState();
}

class _RegisterFormState extends ConsumerState<RegisterForm> {
  static const _welcomeHold = Duration(milliseconds: 1600);

  late final TextEditingController _emailController;
  late final TextEditingController _passwordController;
  late final TextEditingController _confirmPasswordController;
  late final TextEditingController _nameController;
  late final StateProvider<bool> _isPasswordVisible;
  late final StreamSubscription<_RegisterValidation> _validationSub;

  bool _canSubmit = false;
  bool _busy = false;
  bool _showWelcome = false;
  _RegisterFieldError _fieldError = _RegisterFieldError.none;

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController();
    _passwordController = TextEditingController();
    _confirmPasswordController = TextEditingController();
    _nameController = TextEditingController();
    _isPasswordVisible = StateProvider.autoDispose<bool>((ref) => false);

    _validationSub =
        Rx.combineLatest4(
          _nameController.toStream(),
          _emailController.toStream(),
          _passwordController.toStream(),
          _confirmPasswordController.toStream(),
          _validate,
        ).debounceTime(const Duration(milliseconds: 400)).distinct().listen((
          validation,
        ) {
          if (!mounted) return;
          setState(() {
            _canSubmit = validation.canSubmit;
            _fieldError = validation.error;
          });
        });
  }

  static _RegisterValidation _validate(
    String name,
    String email,
    String password,
    String confirm,
  ) {
    final emailOk = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email);
    final passwordOk = password.length >= 8;
    final confirmOk = confirm.isNotEmpty && confirm == password;

    // Only notify once the user has typed something invalid in that field.
    final error = email.isNotEmpty && !emailOk
        ? _RegisterFieldError.email
        : password.isNotEmpty && !passwordOk
        ? _RegisterFieldError.password
        : confirm.isNotEmpty && !confirmOk
        ? _RegisterFieldError.passwordConfirm
        : _RegisterFieldError.none;

    final canSubmit =
        name.trim().isNotEmpty && emailOk && passwordOk && confirmOk;

    return _RegisterValidation(canSubmit: canSubmit, error: error);
  }

  String? get _errorMessage {
    final t = context.translations;
    return switch (_fieldError) {
      _RegisterFieldError.email => t.emailInvalid,
      _RegisterFieldError.password => t.passwordInvalid,
      _RegisterFieldError.passwordConfirm => t.passwordConfirmationInvalid,
      _RegisterFieldError.none => null,
    };
  }

  @override
  void dispose() {
    _validationSub.cancel();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || ref.read(authControllerProvider).isLoading) return;

    FocusScope.of(context).unfocus();
    setState(() => _busy = true);

    final credentials = await ref
        .read(authControllerProvider.notifier)
        .register(
          _nameController.text,
          _emailController.text,
          _passwordController.text,
        );

    if (!mounted) return;

    final authState = ref.read(authControllerProvider);

    if (authState.status == AuthStatus.error || credentials == null) {
      setState(() => _busy = false);

      final errorMessage = switch (authState.errorCode) {
        ErrorCodes.emailAlreadyInUse =>
          context.translations.userEmailAlreadyInUse,
        _ => context.translations.registerUnknownError,
      };

      context.showSnackbar(
        message: errorMessage,
        color: Theme.of(context).colorScheme.error,
      );
      return;
    }

    setState(() => _showWelcome = true);

    await Future.delayed(_welcomeHold);
    if (!mounted) return;

    ref.read(authExitTransitionProvider.notifier).armRegister();
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
          Text(
            context.translations.createAccount,
            style: const TextStyle(fontSize: 16),
          ),
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
    final errorMessage = _errorMessage;
    final isLoading = ref.watch(authControllerProvider).isLoading;
    final buttonActive = _canSubmit || _showWelcome;

    return Column(
      spacing: 16,
      children: [
        FormTextField(
          label: context.translations.usernameForm,
          icon: Icons.person_outline,
          controller: _nameController,
          keyboardType: TextInputType.name,
        ),
        FormTextField(
          label: context.translations.email,
          icon: Icons.email_outlined,
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
        ),
        FormTextField(
          label: context.translations.password,
          icon: Icons.lock_outline,
          controller: _passwordController,
          isPassword: true,
          isPasswordVisible: ref.watch(_isPasswordVisible),
          onPasswordVisibleChanged: (value) {
            ref.read(_isPasswordVisible.notifier).state = value;
          },
        ),
        FormTextField(
          label: context.translations.passwordConfirm,
          icon: Icons.lock_outline,
          controller: _confirmPasswordController,
          isPassword: true,
          isPasswordVisible: ref.watch(_isPasswordVisible),
          onPasswordVisibleChanged: (value) {
            ref.read(_isPasswordVisible.notifier).state = value;
          },
        ),
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 280),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          transitionBuilder: (child, animation) {
            return FadeTransition(
              opacity: animation,
              child: SizeTransition(
                sizeFactor: animation,
                alignment: Alignment.topCenter,
                child: child,
              ),
            );
          },
          child: errorMessage == null
              ? const SizedBox.shrink(key: ValueKey('register-error-empty'))
              : Row(
                  key: ValueKey(errorMessage),
                  mainAxisSize: MainAxisSize.min,
                  spacing: 8,
                  children: [
                    Icon(
                      Icons.error_outline,
                      color: colorScheme.error,
                      size: 20,
                    ),
                    Flexible(
                      child: Text(
                        errorMessage,
                        style: TextStyle(color: colorScheme.error),
                      ),
                    ),
                  ],
                ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: TweenAnimationBuilder<double>(
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

              return ElevatedButton(
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
              );
            },
            child: _buildButtonLabel(isLoading: isLoading),
          ),
        ),
      ],
    );
  }
}
