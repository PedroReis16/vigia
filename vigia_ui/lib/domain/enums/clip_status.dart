enum ClipStatus { receiving, assembling, ready, failed }

extension ClipStatusParsing on ClipStatus {
  static ClipStatus fromApi(String? value) {
    return switch (value) {
      'Receiving' => ClipStatus.receiving,
      'Assembling' => ClipStatus.assembling,
      'Ready' => ClipStatus.ready,
      _ => ClipStatus.failed,
    };
  }
}
