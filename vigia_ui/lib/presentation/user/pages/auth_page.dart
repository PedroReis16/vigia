import 'dart:ui' show lerpDouble;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shell/auth_transition_warm_up.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';
import 'package:vigia_ui/presentation/user/providers/cold_start_provider.dart';
import 'package:vigia_ui/presentation/user/widgets/login_form_widget.dart';
import 'package:vigia_ui/presentation/user/widgets/register_form_widget.dart';

/// Single continuous boot surface:
/// - progress 0 → cold start (centered logo)
/// - progress 1 → auth forms (keyboard-safe scroll)
///
/// No widget-tree swaps between phases — that flicker is visible on devices.
class AuthPage extends ConsumerStatefulWidget {
  const AuthPage({super.key});

  @override
  ConsumerState<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends ConsumerState<AuthPage>
    with SingleTickerProviderStateMixin {
  int _currentPage = 0;
  late final PageController _pageController;
  late final AnimationController _introController;
  late final Animation<double> _introCurved;

  final List<double> _formHeights = [0, 0];

  bool _sessionHandled = false;
  bool _showPipelinePrimer = true;

  static const _introDuration = Duration(milliseconds: 700);
  static const _minColdStartVisible = Duration(milliseconds: 450);

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: 0);

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
    // Keep the invisible primer up for one painted frame, then drop it.
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
    _pageController.dispose();
    super.dispose();
  }

  void _handleSession(AsyncValue<bool> session) {
    if (_sessionHandled || session.isLoading) return;

    _sessionHandled = true;
    final loggedIn = session.asData?.value ?? false;

    if (loggedIn) {
      // Stay at progress 0 (centered logo) until shell morph is armed.
      _prepareAuthenticatedExit();
      return;
    }

    ref.read(coldStartCompletedProvider.notifier).complete();
    _playIntroToAuth();
  }

  Future<void> _playIntroToAuth() async {
    // Let the progress-0 tree settle before ticking — same widget, no swap.
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

    // Logo flight is drawn on the shell morph veil (no Hero).
    ref.read(authExitTransitionProvider.notifier).armColdStart();
    ref.read(coldStartCompletedProvider.notifier).complete();
  }

  void changePage(int page) {
    FocusScope.of(context).unfocus();
    _pageController.animateToPage(
      page,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
    setState(() => _currentPage = page);
  }

  void _onFormHeightChanged(int index, double height) {
    if ((_formHeights[index] - height).abs() < 0.5) return;
    setState(() => _formHeights[index] = height);
  }

  double get _formHeight {
    final target = _formHeights[_currentPage];
    if (target > 0) return target;
    for (final height in _formHeights) {
      if (height > 0) return height;
    }
    return 1;
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(authSessionProvider, (_, next) => _handleSession(next));

    final formHeight = _formHeight;
    final pageWidth = MediaQuery.sizeOf(context).width - 32;
    final primer = _showPipelinePrimer
        ? AuthTransitionWarmUp.pipelinePrimer(context)
        : null;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        // Match veil / AppBar — Theme.primaryColor can diverge under M3.
        backgroundColor: Theme.of(context).colorScheme.primary,
        body: Stack(
          fit: StackFit.expand,
          children: [
            GestureDetector(
              onTap: () => FocusScope.of(context).unfocus(),
              behavior: HitTestBehavior.opaque,
              child: SafeArea(
                child: AnimatedBuilder(
                  animation: _introCurved,
                  builder: (context, _) {
                    return _AuthBootBody(
                      progress: _introCurved.value,
                      formHeight: formHeight,
                      pageWidth: pageWidth,
                      pageController: _pageController,
                      currentPage: _currentPage,
                      onPageChanged: (page) {
                        setState(() => _currentPage = page);
                      },
                      onFormHeightChanged: _onFormHeightChanged,
                      onToggleAuthMode: () {
                        changePage(_currentPage == 0 ? 1 : 0);
                      },
                    );
                  },
                ),
              ),
            ),
            ?primer,
          ],
        ),
      ),
    );
  }
}

/// Progress 0: centered logo (cold start). Progress 1: auth forms + scroll.
class _AuthBootBody extends StatelessWidget {
  const _AuthBootBody({
    required this.progress,
    required this.formHeight,
    required this.pageWidth,
    required this.pageController,
    required this.currentPage,
    required this.onPageChanged,
    required this.onFormHeightChanged,
    required this.onToggleAuthMode,
  });

  final double progress;
  final double formHeight;
  final double pageWidth;
  final PageController pageController;
  final int currentPage;
  final ValueChanged<int> onPageChanged;
  final void Function(int index, double height) onFormHeightChanged;
  final VoidCallback onToggleAuthMode;

  @override
  Widget build(BuildContext context) {
    final t = progress;
    final contentOpacity = const Interval(
      0.18,
      1.0,
      curve: Curves.easeOut,
    ).transform(t);
    final contentSlide = lerpDouble(20, 0, t)!;

    return LayoutBuilder(
      builder: (context, constraints) {
        final logoHeight = VigiaLogoHero.authHeight;
        final centeredGap =
            ((constraints.maxHeight - logoHeight) / 2).clamp(0.0, double.infinity);
        final topGap = lerpDouble(centeredGap, 0.0, t)!;

        return SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          physics: t < 0.99
              ? const NeverScrollableScrollPhysics()
              : null,
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(height: topGap),
                    const _AuthLogo(),
                    // heightFactor collapses form space at t=0 so the logo
                    // stays truly centered during cold start.
                    ClipRect(
                      child: Align(
                        alignment: Alignment.topCenter,
                        heightFactor: t,
                        child: Opacity(
                          opacity: contentOpacity.clamp(0.0, 1.0),
                          child: Transform.translate(
                            offset: Offset(0, contentSlide),
                            child: IgnorePointer(
                              ignoring: contentOpacity < 0.95,
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: AnimatedSize(
                                  duration: const Duration(milliseconds: 300),
                                  curve: Curves.easeInOut,
                                  alignment: Alignment.topCenter,
                                  child: SizedBox(
                                    height: formHeight,
                                    width: double.infinity,
                                    child: PageView(
                                      controller: pageController,
                                      physics:
                                          const NeverScrollableScrollPhysics(),
                                      onPageChanged: onPageChanged,
                                      children: [
                                        _FormPage(
                                          pageWidth: pageWidth,
                                          onHeightChanged: (height) =>
                                              onFormHeightChanged(0, height),
                                          child: const LoginForm(),
                                        ),
                                        _FormPage(
                                          pageWidth: pageWidth,
                                          onHeightChanged: (height) =>
                                              onFormHeightChanged(1, height),
                                          child: const RegisterForm(),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                ClipRect(
                  child: Align(
                    alignment: Alignment.topCenter,
                    heightFactor: t,
                    child: Opacity(
                      opacity: contentOpacity.clamp(0.0, 1.0),
                      child: IgnorePointer(
                        ignoring: contentOpacity < 0.95,
                        child: _AuthModeToggle(
                          currentPage: currentPage,
                          onToggle: onToggleAuthMode,
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

class _AuthModeToggle extends StatelessWidget {
  const _AuthModeToggle({
    required this.currentPage,
    required this.onToggle,
  });

  final int currentPage;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          currentPage == 0
              ? context.translations.noAccount
              : context.translations.hasAccount,
          style: TextStyle(color: Theme.of(context).colorScheme.onPrimary),
        ),
        TextButton(
          style: const ButtonStyle(splashFactory: NoSplash.splashFactory),
          onPressed: onToggle,
          child: Text(
            currentPage == 0
                ? context.translations.register
                : context.translations.login,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onPrimary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }
}

class _AuthLogo extends StatelessWidget {
  const _AuthLogo();

  @override
  Widget build(BuildContext context) {
    // No Hero — enter morph flies the logo on the veil (device-safe).
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

/// Lets a [PageView] child report its intrinsic height while keeping a fixed
/// width matching the page viewport.
class _FormPage extends StatelessWidget {
  const _FormPage({
    required this.pageWidth,
    required this.onHeightChanged,
    required this.child,
  });

  final double pageWidth;
  final ValueChanged<double> onHeightChanged;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return OverflowBox(
      alignment: Alignment.topCenter,
      minHeight: 0,
      maxHeight: double.infinity,
      minWidth: pageWidth,
      maxWidth: pageWidth,
      child: _SizeReporter(
        onSizeChanged: (size) => onHeightChanged(size.height),
        child: child,
      ),
    );
  }
}

class _SizeReporter extends SingleChildRenderObjectWidget {
  const _SizeReporter({required this.onSizeChanged, required super.child});

  final ValueChanged<Size> onSizeChanged;

  @override
  RenderObject createRenderObject(BuildContext context) {
    return _RenderSizeReporter(onSizeChanged);
  }

  @override
  void updateRenderObject(
    BuildContext context,
    covariant _RenderSizeReporter renderObject,
  ) {
    renderObject.onSizeChanged = onSizeChanged;
  }
}

class _RenderSizeReporter extends RenderProxyBox {
  _RenderSizeReporter(this.onSizeChanged);

  ValueChanged<Size> onSizeChanged;
  Size? _oldSize;

  @override
  void performLayout() {
    super.performLayout();
    final newSize = child?.size;
    if (newSize != null && _oldSize != newSize) {
      _oldSize = newSize;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        onSizeChanged(newSize);
      });
    }
  }
}
