import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DeviceClipsPage extends ConsumerWidget {
  const DeviceClipsPage({super.key, required this.deviceId});

  final String deviceId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: Text("Clips")),
      body: ListView(children: [Text("Clips"), Text(deviceId)]),
    );
  }
}
