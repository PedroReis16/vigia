
import 'package:flutter_dotenv/flutter_dotenv.dart';

class Environments {
  static final String apiUrl = dotenv.env["API_URL"] ?? "";

  static final String streamBaseUrl =
      (dotenv.env["STREAM_BASE_URL"] ?? "http://localhost:81")
          .replaceAll(RegExp(r'/+$'), '');
}
