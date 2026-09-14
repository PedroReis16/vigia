import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/dio_provider.dart';
import 'package:vigia_ui/data/repositories/push_token_repository.dart';

part 'push_token_repository_provider.g.dart';

@Riverpod(keepAlive: true)
PushTokenRepository pushTokenRepository(Ref ref) =>
    PushTokenRepository(ref.read(dioProvider));
