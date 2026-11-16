import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/user.dart';
import 'package:vigia_ui/domain/api_asset_url.dart';
import 'package:vigia_ui/domain/profile_initials.dart';
import 'package:vigia_ui/domain/ui_models/user_ui.dart';

void main() {
  test('keeps an absolute picture url', () {
    expect(
      resolveApiAssetUrl('https://cdn.example/pic.jpg'),
      'https://cdn.example/pic.jpg',
    );
    expect(resolveApiAssetUrl('  '), isNull);
  });

  test('member pictures keep a usable url for the avatar', () {
    final model = UserUIModel.fromDTO(
      DeviceUser(
        id: 'user-1',
        name: 'Ana Lima',
        userPicture: 'https://example.test/picture.jpg',
        isOwner: true,
      ),
    );

    expect(model.userPicture, 'https://example.test/picture.jpg');
    expect(profileInitials(model.name, 'ana@vigia.test'), 'AL');
  });
}
