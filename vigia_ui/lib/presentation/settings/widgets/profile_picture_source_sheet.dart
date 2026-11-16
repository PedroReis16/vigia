import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

Future<ImageSource?> showProfilePictureSourceSheet(BuildContext context) {
  return showModalBottomSheet<ImageSource>(
    context: context,
    useRootNavigator: true,
    showDragHandle: true,
    builder: (sheetContext) {
      final t = sheetContext.translations;
      final theme = Theme.of(sheetContext);

      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                child: Text(
                  t.changeProfilePicture,
                  style: theme.textTheme.titleMedium,
                ),
              ),
              ListTile(
                key: const Key('profile-picture-camera'),
                leading: const Icon(Icons.photo_camera_outlined),
                title: Text(t.profilePictureCamera),
                onTap: () => Navigator.of(sheetContext).pop(ImageSource.camera),
              ),
              ListTile(
                key: const Key('profile-picture-gallery'),
                leading: const Icon(Icons.photo_library_outlined),
                title: Text(t.profilePictureGallery),
                onTap: () => Navigator.of(sheetContext).pop(ImageSource.gallery),
              ),
            ],
          ),
        ),
      );
    },
  );
}
