// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Vigia';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get login => 'Sign in';

  @override
  String get register => 'Sign up';

  @override
  String get logout => 'Log out';

  @override
  String get noAccount => 'Don\'t have an account?';

  @override
  String get hasAccount => 'Already have an account?';

  @override
  String get invalidCredentials => 'Invalid username or password';

  @override
  String get loginError => 'Login failed';

  @override
  String get devices => 'Devices';

  @override
  String get settings => 'Settings';

  @override
  String get home => 'Home';

  @override
  String get stage => 'Stage';

  @override
  String sheetRecord(String id) {
    return 'Record #$id';
  }

  @override
  String get noDevicesFound => 'No devices found';

  @override
  String errorWithMessage(String message) {
    return 'Error: $message';
  }

  @override
  String get addDevice => 'Add device';

  @override
  String get scanningHint =>
      'Follow the tutorial and bring your phone close to Vigia. Scanning is already in progress.';

  @override
  String get stepPowerOnTitle => 'Turn on the device';

  @override
  String get stepPowerOnDescription =>
      'Plug Vigia into a power outlet and wait until the light indicates it is ready for setup.';

  @override
  String get stepPairTitle => 'Link to the app';

  @override
  String get stepPairDescription =>
      'Bring your phone close to Vigia to start pairing with the app.';

  @override
  String get stepWaitTitle => 'Wait for confirmation';

  @override
  String get stepWaitDescription =>
      'Wait a few seconds until setup completes successfully.';

  @override
  String get connectingTitle => 'Connecting';

  @override
  String get connectingDescription =>
      'Device found. Establishing a connection with Vigia…';

  @override
  String get authenticatingTitle => 'Validating device';

  @override
  String get authenticatingDescription =>
      'Confirming Vigia\'s identity and authenticating the app…';

  @override
  String get connectionEstablished => 'Connection established';

  @override
  String deviceLinkedSuccess(String deviceName) {
    return '$deviceName was linked successfully.';
  }

  @override
  String get confirm => 'Confirm';

  @override
  String get connectionFailed => 'Could not connect';

  @override
  String get connectionErrorFallback =>
      'An error occurred while searching for or connecting to the device.';

  @override
  String get tryAgain => 'Try again';

  @override
  String get wifiNetwork => 'Wi‑Fi network';

  @override
  String get refreshNetworks => 'Refresh networks';

  @override
  String get selectWifiHint => 'Select the network Vigia should use.';

  @override
  String get manualWifiHintIos => 'On iOS, enter the network name manually.';

  @override
  String get noNetworksFound => 'No networks found. Try refreshing the list.';

  @override
  String get selectOrEnterWifi => 'Select or enter a Wi‑Fi network.';

  @override
  String get networkPassword => 'Network password';

  @override
  String get networkPasswordRequired => 'Enter the network password';

  @override
  String get openNetworkNoPassword => 'Open network — password not required.';

  @override
  String get sendCredentials => 'Send credentials';

  @override
  String get networkSsid => 'Network name (SSID)';

  @override
  String get backToFoundNetworks => 'Back to found networks';

  @override
  String get noNetworksAvailable => 'No networks available';

  @override
  String get enterNetworkManually => 'Enter network manually';

  @override
  String get enterAnotherNetwork => 'Enter another network';

  @override
  String get signalExcellent => 'Excellent signal';

  @override
  String get signalGood => 'Good signal';

  @override
  String get signalFair => 'Fair signal';

  @override
  String get signalWeak => 'Weak signal';
}
