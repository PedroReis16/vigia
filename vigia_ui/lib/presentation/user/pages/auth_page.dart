import 'package:flutter/material.dart';
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

  final List<Widget> _forms = const [LoginForm(), RegisterForm()];

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
    _pageController.animateToPage(
      page,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
    setState(() {
      _currentPage = page;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: Theme.of(context).primaryColor,
        body: SafeArea(
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Hero(
                    tag: VigiaLogoHero.tag,
                    placeholderBuilder: (context, size, child) =>
                        SizedBox(width: size.width, height: size.height),
                    child: Material(
                      type: MaterialType.transparency,
                      child: VigiaLogoHero.image(
                        height: VigiaLogoHero.authHeight,
                      ),
                    ),
                  ),
                ],
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: PageView(
                    controller: _pageController,
                    physics: const NeverScrollableScrollPhysics(),
                    children: _forms,
                  ),
                ),
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
                        color: Theme.of(context).brightness == Brightness.light
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
      ),
    );
  }
}
