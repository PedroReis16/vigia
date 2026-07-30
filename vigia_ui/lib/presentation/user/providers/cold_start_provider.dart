import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'cold_start_provider.g.dart';

/// Whether the app cold-start intro has already run in this process.
///
/// `false` until AuthPage finishes the first boot sequence (intro to forms or
/// redirect to shell). Logout skips cold start because this stays `true`.
@Riverpod(keepAlive: true)
class ColdStartCompleted extends _$ColdStartCompleted {
  @override
  bool build() => false;

  void complete() => state = true;
}
