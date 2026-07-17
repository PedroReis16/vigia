import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AnimatedShellBody extends StatefulWidget {
  final StatefulNavigationShell navigationShell;
  final List<Widget> children;

  const AnimatedShellBody({
    super.key,
    required this.navigationShell,
    required this.children,
  });

  @override
  State<AnimatedShellBody> createState() => _AnimatedShellBodyState();
}

class _AnimatedShellBodyState extends State<AnimatedShellBody> {
  late final PageController _pageController;

  @override
  void initState() {
    super.initState();
    _pageController = PageController(
      initialPage: widget.navigationShell.currentIndex,
    );
  }

  @override
  void didUpdateWidget(AnimatedShellBody oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Tap no bottom nav → anima o PageView
    if (widget.navigationShell.currentIndex !=
        oldWidget.navigationShell.currentIndex) {
      _pageController.animateToPage(
        widget.navigationShell.currentIndex,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PageView(
      controller: _pageController,
      onPageChanged: (index) {
        // Swipe entre abas → atualiza a rota
        widget.navigationShell.goBranch(index);
      },
      children: widget.children,
    );
  }
}
