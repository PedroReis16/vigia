import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:skeletonizer/skeletonizer.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_card.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/devices/widgets/new_device_modal.dart';
import 'package:vigia_ui/presentation/shared/widgets/custom_refresh_indicator.dart';
import 'package:vigia_ui/presentation/user/widgets/devices_load_erro.dart';

class DevicesPage extends ConsumerWidget {
  const DevicesPage({super.key});

  static const _scrollPhysics = AlwaysScrollableScrollPhysics(
    parent: ClampingScrollPhysics(),
  );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 280),
        switchInCurve: Curves.easeOut,
        switchOutCurve: Curves.easeIn,
        child: CustomRefreshIndicator(
          enabled: !ref.watch(devicesProvider).hasError,
          onRefresh: () => ref.read(devicesProvider.notifier).refresh(),
          useIndicator: false,
          child: Consumer(
            builder: (context, ref, _) => _loadDevices(context, ref),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showModalBottomSheet(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _loadDevices(BuildContext context, WidgetRef ref) {
    final devicesAsync = ref.watch(devicesProvider);

    return devicesAsync.when(
      loading: () => Skeletonizer(
        child: ListView.builder(
          physics: _scrollPhysics,
          itemCount: 3,
          itemBuilder: (context, index) {
            return DeviceCard(
              device: DeviceUIModel(
                id: 'skeleton-$index',
                name: 'Device posicionado na sala',
                nickname: 'Device posicionado na sala',
                isOwner: false,
                room: DeviceRooms.livingRoom,
              ),
            );
          },
        ),
      ),
      error: (error, stackTrace) => DevicesLoadError(
        onTryAgain: () => ref.read(devicesProvider.notifier).refresh(),
      ),
      data: (devices) {
        if (devices.isEmpty) {
          return ListView(
            key: const ValueKey('devices-empty'),
            physics: _scrollPhysics,
            children: [
              SizedBox(
                height: MediaQuery.sizeOf(context).height * 0.6,
                child: Center(child: Text(context.translations.noDevicesFound)),
              ),
            ],
          );
        }

        return ListView(
          physics: _scrollPhysics,
          children: [
            for (final device in devices)
              DeviceCard(
                device: device,
                onTap: () {
                  context.push(
                    AppRoutes.deviceDetailsPage.replaceAll(
                      ':deviceId',
                      device.id,
                    ),
                    extra: device,
                  );
                },
              ),
          ],
        );
      },
    );
  }

  Future<T?> _showModalBottomSheet<T>(BuildContext context) =>
      showModalBottomSheet<T>(
        context: context,
        useRootNavigator: true,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (context) {
          final media = MediaQuery.of(context);
          return Padding(
            padding: EdgeInsets.only(bottom: media.viewInsets.bottom),
            child: SizedBox(
              height: media.size.height * 0.65,
              width: media.size.width,
              child: const NewDeviceModal(),
            ),
          );
        },
      );
}
