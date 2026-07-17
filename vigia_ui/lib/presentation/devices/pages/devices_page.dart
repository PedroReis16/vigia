import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_card.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/devices/widgets/new_device_modal.dart';

class DevicesPage extends ConsumerWidget {
  const DevicesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Consumer(builder: (context, ref, _) => _loadDevices(context, ref)),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          showModalBottomSheet(
            context: context,
            useRootNavigator: true,
            isScrollControlled: true,
            showDragHandle: true,
            builder: (context) => SizedBox(
              height: MediaQuery.of(context).size.height * 0.65,
              width: MediaQuery.of(context).size.width,
              child: const NewDeviceModal(),
            ),
          );
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
                context.push(
                  AppRoutes.deviceDetails.replaceAll(
                    ':deviceId',
                    devices[index].id,
                  ),
                );
              },
            );
          },
        );
      },
    );
  }
}
