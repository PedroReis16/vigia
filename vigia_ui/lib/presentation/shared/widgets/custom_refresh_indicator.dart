import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Pull-to-refresh that reveals an arrow by drag progress and, past the
/// threshold, shows [releaseLabel] until the user releases to refresh.
class CustomRefreshIndicator extends StatefulWidget {
  const CustomRefreshIndicator({
    super.key,
    required this.onRefresh,
    required this.child,
    this.triggerOffset = 72,
    this.maxOffset = 112,
    this.releaseLabel = 'Solte para atualizar a listagem',
    this.useIndicator = true,
    this.enabled = true,
  });

  final Future<void> Function() onRefresh;
  final Widget child;

  /// Distance the user must pull before release triggers [onRefresh].
  final double triggerOffset;

  /// Caps how far the indicator area can grow while dragging.
  final double maxOffset;

  final String releaseLabel;

  /// When true, keeps a spinner in the pull header until [onRefresh] completes.
  /// When false, collapses immediately so the page can show its own loading UI.
  final bool useIndicator;

  /// When false, pull-to-refresh gestures are ignored and [onRefresh] is never called.
  final bool enabled;

  @override
  State<CustomRefreshIndicator> createState() => _CustomRefreshIndicatorState();
}

class _CustomRefreshIndicatorState extends State<CustomRefreshIndicator> {
  double _pullOffset = 0;
  bool _refreshing = false;

  double get _progress => (_pullOffset / widget.triggerOffset).clamp(0.0, 1.0);

  bool get _armed => _pullOffset >= widget.triggerOffset;

  double get _indicatorExtent {
    if (_refreshing) {
      return widget.useIndicator ? widget.triggerOffset : 0;
    }
    return _pullOffset;
  }

  @override
  void didUpdateWidget(covariant CustomRefreshIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!widget.enabled && (_pullOffset > 0 || _refreshing)) {
      setState(() {
        _pullOffset = 0;
        _refreshing = false;
      });
    }
  }

  bool _onScrollNotification(ScrollNotification notification) {
    if (!widget.enabled || _refreshing) return false;
    if (notification.metrics.axis != Axis.vertical) return false;

    // Clamped lists report past-edge drag as OverscrollNotification.
    if (notification is OverscrollNotification &&
        notification.dragDetails != null &&
        notification.overscroll < 0) {
      _setPull(_pullOffset - notification.overscroll);
      return false;
    }

    // Bouncing lists expose negative pixels while overscrolled at the top.
    if (notification is ScrollUpdateNotification) {
      final leadingOverscroll =
          notification.metrics.minScrollExtent - notification.metrics.pixels;
      if (leadingOverscroll > 0) {
        _setPull(leadingOverscroll);
      } else if (_pullOffset > 0 &&
          notification.dragDetails != null &&
          (notification.scrollDelta ?? 0) > 0) {
        _setPull(_pullOffset - notification.scrollDelta!);
      }
    }

    if (notification is ScrollEndNotification) {
      _onReleased();
    }

    return false;
  }

  void _setPull(double value) {
    final next = value.clamp(0.0, widget.maxOffset);
    if (next == _pullOffset) return;
    setState(() => _pullOffset = next);
  }

  Future<void> _onReleased() async {
    if (!widget.enabled || _refreshing) return;

    if (_armed) {
      setState(() {
        _refreshing = true;
        // Keep header open only when this widget owns the loading UI.
        _pullOffset = widget.useIndicator ? widget.triggerOffset : 0;
      });
      try {
        await widget.onRefresh();
      } finally {
        if (mounted) {
          setState(() {
            _refreshing = false;
            _pullOffset = 0;
          });
        }
      }
      return;
    }

    if (_pullOffset > 0) {
      setState(() => _pullOffset = 0);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Column(
      children: [
        AnimatedContainer(
          duration: _refreshing || _pullOffset == 0
              ? const Duration(milliseconds: 200)
              : Duration.zero,
          curve: Curves.easeOut,
          height: _indicatorExtent,
          width: double.infinity,
          alignment: Alignment.center,
          child: _buildIndicator(colors),
        ),
        Expanded(
          child: NotificationListener<ScrollNotification>(
            onNotification: _onScrollNotification,
            child: widget.child,
          ),
        ),
      ],
    );
  }

  Widget _buildIndicator(ColorScheme colors) {
    if (_indicatorExtent <= 0) return const SizedBox.shrink();

    if (_refreshing) {
      if (!widget.useIndicator) return const SizedBox.shrink();
      return SizedBox(
        width: 22,
        height: 22,
        child: CircularProgressIndicator(
          strokeWidth: 2.5,
          color: colors.primary,
        ),
      );
    }

    if (_armed) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Text(
          widget.releaseLabel,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: colors.primary,
            fontWeight: FontWeight.w600,
          ),
        ),
      );
    }

    return Opacity(
      opacity: Curves.easeOut.transform(_progress),
      child: Transform.rotate(
        angle: _progress * math.pi,
        child: Transform.scale(
          scale: 0.6 + (0.4 * _progress),
          child: Icon(
            Icons.arrow_downward_rounded,
            color: colors.primary,
            size: 28,
          ),
        ),
      ),
    );
  }
}
