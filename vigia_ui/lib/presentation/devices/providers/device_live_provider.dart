import 'package:vigia_ui/domain/environments.dart';

String deviceStreamUrl(String deviceId) =>
    '${Environments.streamBaseUrl}/live/$deviceId';

String deviceWhepUrl(String deviceId) => '${deviceStreamUrl(deviceId)}/whep';
