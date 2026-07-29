class RequestException implements Exception {
  final String message;

  RequestException(this.message);

  @override
  String toString() {
    return 'RequestException: $message';
  }
}
