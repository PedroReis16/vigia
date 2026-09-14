import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'pending_invite_provider.g.dart';

@Riverpod(keepAlive: true)
class PendingInviteToken extends _$PendingInviteToken {
  @override
  String? build() => null;

  void setToken(String? token) => state = token;

  void clear() => state = null;
}
