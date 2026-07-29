import 'package:flutter/material.dart';

class FormTextField extends StatefulWidget {
  final String label;
  final IconData icon;
  final TextEditingController controller;
  final bool isPassword;
  final bool? isPasswordVisible;
  final void Function(bool)? onPasswordVisibleChanged;
  final TextInputType? keyboardType;

  const FormTextField({
    super.key,
    required this.label,
    required this.icon,
    required this.controller,
    this.isPassword = false,
    this.isPasswordVisible,
    this.onPasswordVisibleChanged,
    this.keyboardType = TextInputType.text,
  });

  @override
  State<FormTextField> createState() => _FormTextFieldState();
}

class _FormTextFieldState extends State<FormTextField> {
  late bool _isPasswordVisible;

  bool get _isVisibilityControlled => widget.isPasswordVisible != null;

  @override
  void initState() {
    super.initState();
    _isPasswordVisible = widget.isPasswordVisible ?? false;
  }

  @override
  void didUpdateWidget(covariant FormTextField oldWidget) {
    super.didUpdateWidget(oldWidget);
    // When the parent owns visibility, sync local state with the new prop.
    if (_isVisibilityControlled &&
        widget.isPasswordVisible != oldWidget.isPasswordVisible) {
      _isPasswordVisible = widget.isPasswordVisible!;
    }
  }

  void _togglePasswordVisibility() {
    final next = !_isPasswordVisible;
    if (_isVisibilityControlled) {
      widget.onPasswordVisibleChanged?.call(next);
      return;
    }
    setState(() => _isPasswordVisible = next);
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    const borderRadius = BorderRadius.all(Radius.circular(10));
    final isPasswordVisible = _isVisibilityControlled
        ? widget.isPasswordVisible!
        : _isPasswordVisible;

    // Matches AuthPage scaffold (primary) so the outline disappears at rest.
    final hiddenBorder = OutlineInputBorder(
      borderRadius: borderRadius,
      borderSide: BorderSide(color: colorScheme.surface),
    );
    final focusedBorder = OutlineInputBorder(
      borderRadius: borderRadius,
      borderSide: BorderSide(color: colorScheme.surface, width: 2),
    );

    return TextField(
      controller: widget.controller,
      obscureText: widget.isPassword && !isPasswordVisible,
      cursorColor: colorScheme.onPrimary,
      keyboardType: widget.keyboardType,
      decoration: InputDecoration(
        filled: true,
        fillColor: colorScheme.surface,
        prefixIcon: Icon(widget.icon, color: colorScheme.onSurfaceVariant),
        labelText: widget.label,
        labelStyle: TextStyle(color: colorScheme.onSurfaceVariant),
        floatingLabelBehavior: FloatingLabelBehavior.auto,
        floatingLabelStyle: TextStyle(
          color: colorScheme.onSurface,
          fontWeight: FontWeight.w500,
        ),
        border: hiddenBorder,
        enabledBorder: hiddenBorder,
        focusedBorder: focusedBorder,
        suffixIcon: widget.isPassword
            ? IconButton(
                style: const ButtonStyle(splashFactory: NoSplash.splashFactory),
                onPressed: _togglePasswordVisibility,
                icon: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  transitionBuilder: (child, animation) =>
                      ScaleTransition(scale: animation, child: child),
                  child: !isPasswordVisible
                      ? const Icon(key: ValueKey(1), Icons.visibility_outlined)
                      : const Icon(
                          key: ValueKey(2),
                          Icons.visibility_off_outlined,
                        ),
                ),
              )
            : null,
      ),
    );
  }
}
