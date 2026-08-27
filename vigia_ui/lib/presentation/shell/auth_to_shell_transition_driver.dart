import 'package:flutter/material.dart';
import 'package:vigia_ui/presentation/shell/auth_to_shell_transition.dart';
import 'package:vigia_ui/presentation/shell/auth_transition_warm_up.dart';

/// Drives [AuthToShellTransition] with a local [AnimationController].
///
/// GoRouter's route [animation] can complete in the same frame on physical
/// devices (declarative page updates), which skips the morph. The local
/// controller always plays 0→1 so the veil covers the shell from the first
/// frame and shrinks to the AppBar regardless of the route animation.
///
/// The controller stays at 0 until logos are precached and one extra frame has
/// painted — otherwise the first morph on device pays decode/pipeline cost
/// mid-flight (later runs look fine because caches are warm).
class AuthToShellTransitionDriver extends StatefulWidget {
  const AuthToShellTransitionDriver({
    super.key,
    required this.child,
    this.reverse = false,
    this.flyLogo = false,
    this.logoFromCenter = false,
  });

  final Widget child;
  final bool reverse;
  final bool flyLogo;
  final bool logoFromCenter;

  @override
  State<AuthToShellTransitionDriver> createState() =>
      _AuthToShellTransitionDriverState();
}

class _AuthToShellTransitionDriverState
    extends State<AuthToShellTransitionDriver>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: AuthToShellTransition.duration,
    );
    WidgetsBinding.instance.addPostFrameCallback((_) => _startWhenReady());
  }

  Future<void> _startWhenReady() async {
    if (!mounted) return;
    await AuthTransitionWarmUp.precacheLogos(context);
    if (!mounted) return;
    // Let the t=0 veil (and flyLogo) paint once with warm caches.
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AuthToShellTransition(
      animation: _controller,
      reverse: widget.reverse,
      flyLogo: widget.flyLogo,
      logoFromCenter: widget.logoFromCenter,
      child: widget.child,
    );
  }
}
