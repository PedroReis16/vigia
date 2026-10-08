import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/keycloak_auth_client_provider.dart';
import 'package:vigia_ui/data/repositories/auth_repository.dart';

part 'auth_repository_provider.g.dart';

@riverpod
AuthRepository authRepository(Ref ref) =>
    AuthRepository(ref.watch(keycloakAuthClientProvider));
