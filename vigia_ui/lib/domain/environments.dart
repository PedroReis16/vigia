

import 'package:flutter_dotenv/flutter_dotenv.dart';

class Environments {
  static final String apiUrl = dotenv.env["API_URL"] ?? "";
}