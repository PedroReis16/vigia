import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/core/providers/dio_provider.dart';
import 'package:vigia_ui/data/repositories/user_profile_repository.dart';
import 'package:vigia_ui/domain/DTOs/user_profile.dart';

final userProfileRepositoryProvider = Provider<UserProfileRepository>(
  (ref) => UserProfileRepository(ref.watch(dioProvider)),
);

final userProfileProvider =
    AsyncNotifierProvider<UserProfileController, UserProfile>(
      UserProfileController.new,
    );

class UserProfileController extends AsyncNotifier<UserProfile> {
  @override
  Future<UserProfile> build() {
    return ref.read(userProfileRepositoryProvider).getProfile();
  }

  Future<void> upload(
    Uint8List bytes,
    String filename,
    String contentType,
  ) async {
    final profile = await ref
        .read(userProfileRepositoryProvider)
        .uploadPicture(bytes, filename, contentType);
    state = AsyncData(profile);
  }

  Future<void> remove() async {
    final profile = await ref
        .read(userProfileRepositoryProvider)
        .removePicture();
    state = AsyncData(profile);
  }

  Future<void> save({
    required String firstName,
    required String lastName,
    required String phone,
  }) async {
    final profile = await ref
        .read(userProfileRepositoryProvider)
        .updateProfile(firstName: firstName, lastName: lastName, phone: phone);
    state = AsyncData(profile);
  }

  Future<void> delete() {
    return ref.read(userProfileRepositoryProvider).deleteAccount();
  }
}
