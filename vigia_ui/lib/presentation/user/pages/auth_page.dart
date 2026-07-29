import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/core/theme/theme_colors.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';
import 'package:vigia_ui/presentation/user/widgets/login_form_widget.dart';
import 'package:vigia_ui/presentation/user/widgets/register_form_widget.dart';

class AuthPage extends ConsumerStatefulWidget {
  const AuthPage({super.key});

  @override
  ConsumerState<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends ConsumerState<AuthPage> {
  int _currentPage = 0;
  late final PageController _pageController;

  final List<double> _formHeights = [0, 0];

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: 0);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void changePage(int page) {
    FocusScope.of(context).unfocus();
    _pageController.animateToPage(
      page,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
    setState(() {
      _currentPage = page;
    });
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
    final formHeight = _formHeight;
    final pageWidth =
        MediaQuery.sizeOf(context).width - 32; // horizontal padding

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: Theme.of(context).primaryColor,
        body: GestureDetector(
          onTap: () => FocusScope.of(context).unfocus(),
          behavior: HitTestBehavior.opaque,
          child: SafeArea(
            child: LayoutBuilder(
              builder: (context, constraints) {
                return SingleChildScrollView(
                  keyboardDismissBehavior:
                      ScrollViewKeyboardDismissBehavior.onDrag,
                  child: ConstrainedBox(
                    constraints: BoxConstraints(
                      minHeight: constraints.maxHeight,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Hero(
                                  tag: VigiaLogoHero.tag,
                                  placeholderBuilder: (context, size, child) =>
                                      SizedBox(
                                        width: size.width,
                                        height: size.height,
                                      ),
                                  child: Material(
                                    type: MaterialType.transparency,
                                    child: VigiaLogoHero.image(
                                      height: VigiaLogoHero.authHeight,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            Padding(
                              padding: const EdgeInsets.all(16),
                              child: AnimatedSize(
                                duration: const Duration(milliseconds: 300),
                                curve: Curves.easeInOut,
                                alignment: Alignment.topCenter,
                                child: SizedBox(
                                  height: formHeight,
                                  width: double.infinity,
                                  child: PageView(
                                    controller: _pageController,
                                    physics:
                                        const NeverScrollableScrollPhysics(),
                                    onPageChanged: (page) {
                                      setState(() => _currentPage = page);
                                    },
                                    children: [
                                      _FormPage(
                                        pageWidth: pageWidth,
                                        onHeightChanged: (height) =>
                                            _onFormHeightChanged(0, height),
                                        child: const LoginForm(),
                                      ),
                                      _FormPage(
                                        pageWidth: pageWidth,
                                        onHeightChanged: (height) =>
                                            _onFormHeightChanged(1, height),
                                        child: const RegisterForm(),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              _currentPage == 0
                                  ? context.translations.noAccount
                                  : context.translations.hasAccount,
                              style: TextStyle(color: Colors.white),
                            ),
                            TextButton(
                              style: const ButtonStyle(
                                splashFactory: NoSplash.splashFactory,
                              ),
                              onPressed: () {
                                changePage(_currentPage == 0 ? 1 : 0);
                              },
                              child: Text(
                                _currentPage == 0
                                    ? context.translations.register
                                    : context.translations.login,
                                style: TextStyle(
                                  color:
                                      Theme.of(context).brightness ==
                                          Brightness.light
                                      ? context.appColors.outline
                                      : context.appColors.primary,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ),
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
