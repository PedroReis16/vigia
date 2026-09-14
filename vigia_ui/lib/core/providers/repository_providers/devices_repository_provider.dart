import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/dio_provider.dart';
import 'package:vigia_ui/data/repositories/devices_repository.dart';

part 'devices_repository_provider.g.dart';

@riverpod
DevicesRepository devicesRepository(Ref ref) =>
    DevicesRepository(ref.read(dioProvider));
