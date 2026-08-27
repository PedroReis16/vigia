class WifiNetwork {
  const WifiNetwork({
    required this.ssid,
    required this.signalLevel,
    required this.isSecure,
  });

  final String ssid;
  final int signalLevel;
  final bool isSecure;
}
