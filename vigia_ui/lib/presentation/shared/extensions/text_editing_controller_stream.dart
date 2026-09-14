import 'package:flutter/widgets.dart';

extension TextEditingControllerStream on TextEditingController {
  /// Emits the current [text] on every change, including the initial value.
  Stream<String> toStream() {
    return Stream<String>.multi((controller) {
      void onChanged() => controller.add(text);
      addListener(onChanged);
      controller
        ..add(text)
        ..onCancel = () => removeListener(onChanged);
    });
  }
}
