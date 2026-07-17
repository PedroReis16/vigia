import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/presentation/devices/device_card.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';

class DevicesPage extends ConsumerWidget {
  const DevicesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Consumer(builder: (context, ref, _) => _loadDevices(context, ref)),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          print('onPressed');
        },
        child: Icon(Icons.add),
      ),
    );
  }

  Widget _loadDevices(BuildContext context, WidgetRef ref) {
    final devicesAsync = ref.watch(getDevicesProvider);

    return devicesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stackTrace) =>
          Center(child: Text('Error: ${error.toString()}')),
      data: (devices) {
        if (devices.isEmpty) return Center(child: Text('No devices found'));
        return ListView.builder(
          itemCount: devices.length,
          itemBuilder: (context, index) {
            return DeviceCard(
              device: devices[index],
              onTap: () {
                print('onTap');
              },
            );
          },
        );
      },
    );
  }
}
