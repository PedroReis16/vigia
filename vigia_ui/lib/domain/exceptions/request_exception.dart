import 'package:vigia_ui/domain/enums/error_codes.dart';

class RequestException implements Exception {
  final String message;
  final ErrorCodes? errorCode;
  RequestException({
    required this.message,
    this.errorCode = ErrorCodes.unknownError,
  });

  @override
  String toString() {
    return 'RequestException: $message';
  }
}
