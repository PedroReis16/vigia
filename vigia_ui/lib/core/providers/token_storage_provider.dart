import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/data/services/token_storage_service.dart';

part 'token_storage_provider.g.dart';

@Riverpod(keepAlive: true)
TokenStorageService tokenStorage(Ref ref) => TokenStorageService();
