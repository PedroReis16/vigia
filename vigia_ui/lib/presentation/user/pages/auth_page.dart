import 'dart:ui' show lerpDouble;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/domain/environments.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shared/extensions/show_snackbar.dart';
import 'package:vigia_ui/presentation/shell/auth_transition_warm_up.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';
import 'package:vigia_ui/presentation/user/providers/cold_start_provider.dart';
import 'package:vigia_ui/presentation/user/widgets/keycloak_login_sheet.dart';

/// Single continuous boot surface:
/// - progress 0 → cold start (centered logo)
/// - progress 1 → logo and the Keycloak entry button
///
/// No widget-tree swaps between phases — that flicker is visible on devices.
class AuthPage extends ConsumerStatefulWidget {
  const AuthPage({super.key});

  @override
  ConsumerState<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends ConsumerState<AuthPage>
    with SingleTickerProviderStateMixin {
  late final AnimationController _introController;
  late final Animation<double> _introCurved;

  bool _sessionHandled = false;
  bool _showPipelinePrimer = true;
  bool _openingLogin = false;

  static const _introDuration = Duration(milliseconds: 700);
  static const _minColdStartVisible = Duration(milliseconds: 450);

  @override
  void initState() {
    super.initState();

    final coldStartDone = ref.read(coldStartCompletedProvider);

    _introController = AnimationController(
      vsync: this,
      duration: _introDuration,
      value: coldStartDone ? 1.0 : 0.0,
    );
    _introCurved = CurvedAnimation(
      parent: _introController,
      curve: Curves.easeInOutCubic,
    );

    if (coldStartDone) {
      _sessionHandled = true;
    }

    WidgetsBinding.instance.addPostFrameCallback(
      (_) => _warmUpThenBoot(coldStartDone),
    );
  }

  Future<void> _warmUpThenBoot(bool coldStartDone) async {
    if (!mounted) return;
    await AuthTransitionWarmUp.precacheLogos(context);
    if (!mounted) return;
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    AuthTransitionWarmUp.markPipelinesPainted();
    setState(() => _showPipelinePrimer = false);

    if (coldStartDone) return;
    _handleSession(ref.read(authSessionProvider));
  }

  @override
  void dispose() {
    _introController.dispose();
    super.dispose();
  }

  void _handleSession(AsyncValue<bool> session) {
    if (_sessionHandled || session.isLoading) return;

    _sessionHandled = true;
    final loggedIn = session.asData?.value ?? false;

    if (loggedIn) {
      _prepareAuthenticatedExit();
      return;
    }

    ref.read(coldStartCompletedProvider.notifier).complete();
    _playIntroToAuth();
  }

  Future<void> _playIntroToAuth() async {
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    await _introController.forward();
  }

  Future<void> _prepareAuthenticatedExit() async {
    final started = DateTime.now();

    await AuthTransitionWarmUp.precacheLogos(context);
    if (!mounted) return;

    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;

    final elapsed = DateTime.now().difference(started);
    final remaining = _minColdStartVisible - elapsed;
    if (remaining > Duration.zero) {
      await Future<void>.delayed(remaining);
      if (!mounted) return;
    }

    ref.read(authExitTransitionProvider.notifier).armColdStart();
    ref.read(coldStartCompletedProvider.notifier).complete();
  }

  Future<void> _openKeycloak() async {
    if (_openingLogin) return;
    if (Environments.keycloakUrl.isEmpty) {
      _showLoginError();
      return;
    }

    setState(() => _openingLogin = true);
    final outcome = await showModalBottomSheet<KeycloakLoginOutcome>(
      context: context,
      useRootNavigator: true,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        final media = MediaQuery.of(context);
        return Padding(
          padding: EdgeInsets.only(bottom: media.viewInsets.bottom),
          child: SizedBox(
            height: media.size.height * 0.92,
            width: media.size.width,
            child: const KeycloakLoginSheet(),
          ),
        );
      },
    );
    if (!mounted) return;
    setState(() => _openingLogin = false);

    if (outcome is! KeycloakLoginSuccess) {
      if (outcome is KeycloakLoginFailure) _showLoginError();
      return;
    }

    ref.read(authExitTransitionProvider.notifier).armLogin();
    await ref
        .read(authControllerProvider.notifier)
        .commitSession(outcome.credentials);
  }

  void _showLoginError() {
    context.showSnackbar(
      message: context.translations.loginError,
      color: Theme.of(context).colorScheme.error,
    );
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(authSessionProvider, (_, next) => _handleSession(next));

    final primer = _showPipelinePrimer
        ? AuthTransitionWarmUp.pipelinePrimer(context)
        : null;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: Theme.of(context).colorScheme.primary,
        body: Stack(
          fit: StackFit.expand,
          children: [
            SafeArea(
              child: AnimatedBuilder(
                animation: _introCurved,
                builder: (context, _) {
                  return _AuthBootBody(
                    progress: _introCurved.value,
                    onEnter: _openingLogin ? null : _openKeycloak,
                  );
                },
              ),
            ),
            ?primer,
          ],
        ),
      ),
    );
  }
}

/// Progress 0: centered logo (cold start). Progress 1: logo + Entrar.
class _AuthBootBody extends StatelessWidget {
  const _AuthBootBody({required this.progress, required this.onEnter});

  final double progress;
  final VoidCallback? onEnter;

  @override
  Widget build(BuildContext context) {
    final t = progress;
    final contentOpacity = const Interval(
      0.18,
      1.0,
      curve: Curves.easeOut,
    ).transform(t);

    return LayoutBuilder(
      builder: (context, constraints) {
        final logoHeight = VigiaLogoHero.authHeight;
        final centeredGap = ((constraints.maxHeight - logoHeight) / 2).clamp(
          0.0,
          double.infinity,
        );
        final topGap = lerpDouble(centeredGap, 0.0, t)!;

        return SingleChildScrollView(
          physics: t < 0.99 ? const NeverScrollableScrollPhysics() : null,
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Column(
              children: [
                SizedBox(height: topGap),
                const _AuthLogo(),
                ClipRect(
                  child: Align(
                    alignment: Alignment.topCenter,
                    heightFactor: t,
                    child: Opacity(
                      opacity: contentOpacity.clamp(0.0, 1.0),
                      child: IgnorePointer(
                        ignoring: contentOpacity < 0.95,
                        child: Padding(
                          padding: const EdgeInsets.fromLTRB(16, 24, 16, 16),
                          child: _EnterButton(onPressed: onEnter),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _EnterButton extends StatelessWidget {
  const _EnterButton({required this.onPressed});

  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return ElevatedButton(
      key: const Key('auth-enter'),
      onPressed: onPressed,
      style: ButtonStyle(
        maximumSize: WidgetStateProperty.all(const Size(double.infinity, 50)),
        minimumSize: WidgetStateProperty.all(const Size(double.infinity, 50)),
        padding: WidgetStateProperty.all(
          const EdgeInsets.symmetric(horizontal: 16),
        ),
        shape: WidgetStateProperty.all(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
        backgroundColor: WidgetStateProperty.all(colorScheme.secondary),
        foregroundColor: WidgetStateProperty.all(colorScheme.onSecondary),
      ),
      child: Text(
        context.translations.login,
        style: const TextStyle(fontSize: 16),
      ),
    );
  }
}

class _AuthLogo extends StatelessWidget {
  const _AuthLogo();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Material(
          type: MaterialType.transparency,
          child: VigiaLogoHero.image(height: VigiaLogoHero.authHeight),
        ),
      ],
    );
  }
}
