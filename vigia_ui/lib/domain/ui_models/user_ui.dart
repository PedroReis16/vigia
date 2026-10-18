import 'package:vigia_ui/domain/DTOs/user.dart';
import 'package:vigia_ui/domain/api_asset_url.dart';

class UserUIModel {
  final String id;
  final String name;
  final String? userPicture;
  final bool isOwner;

  UserUIModel({
    required this.id,
    required this.name,
    this.userPicture,
    required this.isOwner,
  });

  static UserUIModel fromDTO(DeviceUser user) {
    return UserUIModel(
      id: user.id,
      name: user.name,
      userPicture: resolveApiAssetUrl(user.userPicture),
      isOwner: user.isOwner,
    );
  }
}
