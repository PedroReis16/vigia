import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/core/app_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/enums/auth_status.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/user/providers/auth_provider.dart';

class LoginForm extends ConsumerStatefulWidget {
  const LoginForm({super.key});

  @override
  ConsumerState<ConsumerStatefulWidget> createState() => _LoginFormState();
}

class _LoginFormState extends ConsumerState<LoginForm> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TextField(
          controller: _emailController,
          decoration: InputDecoration(labelText: context.translations.email),
        ),
        Padding(
          padding: const EdgeInsetsGeometry.symmetric(vertical: 16),
          child: TextField(
            controller: _passwordController,
            decoration: InputDecoration(
              labelText: context.translations.password,
            ),
          ),
        ),
        ElevatedButton(
          onPressed: ref.watch(authControllerProvider).isLoading
              ? null
              : () async {
                  await ref
                      .read(authControllerProvider.notifier)
                      .login(_emailController.text, _passwordController.text);

                  final status = ref.watch(authControllerProvider).status;

                  switch (status) {
                    case AuthStatus.unauthorized:
                      _showSnackBar(
                        // ignore: use_build_context_synchronously
                        context,
                        // ignore: use_build_context_synchronously
                        context.translations.invalidCredentials,
                        // ignore: use_build_context_synchronously
                        Theme.of(context).colorScheme.error,
                      );
                      break;
                    case AuthStatus.error:
                      _showSnackBar(
                        // ignore: use_build_context_synchronously
                        context,
                        // ignore: use_build_context_synchronously
                        context.translations.loginError,
                        // ignore: use_build_context_synchronously
                        Theme.of(context).colorScheme.error,
                      );
                      break;
                    case AuthStatus.authorized:
                      ref.read(appRouterProvider).go(AppRoutes.devicesPage);
                      break;
                    default:
                      break;
                  }
                },
          style: ButtonStyle(
            maximumSize: WidgetStateProperty.all(Size(double.infinity, 50)),
            minimumSize: WidgetStateProperty.all(Size(double.infinity, 50)),
            padding: WidgetStateProperty.all(EdgeInsets.zero),
            shape: WidgetStateProperty.all(
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
          ),
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
