import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
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
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _loadDevices(BuildContext context, WidgetRef ref) {
    final devicesAsync = ref.watch(devicesProvider);

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 280),
      switchInCurve: Curves.easeOut,
      switchOutCurve: Curves.easeIn,
      child: devicesAsync.when(
        loading: () => const Center(
          key: ValueKey('devices-loading'),
          child: CircularProgressIndicator(),
        ),
        error: (error, stackTrace) => Center(
          key: const ValueKey('devices-error'),
          child: Text(context.translations.errorWithMessage(error.toString())),
        ),
        data: (devices) {
          if (devices.isEmpty) {
            return Center(
              key: const ValueKey('devices-empty'),
              child: Text(context.translations.noDevicesFound),
            );
          }
          return ListView.builder(
            key: const ValueKey('devices-list'),
            itemCount: devices.length,
            itemBuilder: (context, index) {
              return DeviceCard(
                device: devices[index],
                onTap: () {
                  context.push(
                    AppRoutes.deviceStreamPage.replaceAll(
                      ':deviceId',
                      devices[index].id,
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}
