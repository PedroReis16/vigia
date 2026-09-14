import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/token_storage_provider.dart';
import 'package:vigia_ui/data/interceptors/auth_interceptor.dart';
import 'package:vigia_ui/domain/environments.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'dio_provider.g.dart';

@Riverpod(keepAlive: true)
Dio dio(Ref ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  final dio = Dio(BaseOptions(baseUrl: Environments.apiUrl));
  final refreshDio = Dio(BaseOptions(baseUrl: Environments.apiUrl));

  dio.interceptors.add(
    AuthInterceptor(
      dio: dio,
      refreshDio: refreshDio,
      tokenStorage: tokenStorage,
      onRefreshFailed: () =>
          ref.read(authSessionProvider.notifier).clearSession(),
    ),
  );

  return dio;
}
