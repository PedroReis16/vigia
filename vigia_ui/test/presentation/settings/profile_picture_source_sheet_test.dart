import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';
import 'package:vigia_ui/presentation/settings/widgets/profile_picture_source_sheet.dart';

import '../../helpers/pump_app.dart';

void main() {
  testWidgets('asks for camera or gallery before changing the photo', (
    tester,
  ) async {
    ImageSource? source;

    await pumpApp(
      tester,
      child: Builder(
        builder: (context) => TextButton(
          onPressed: () async {
            source = await showProfilePictureSourceSheet(context);
          },
          child: const Text('open'),
        ),
      ),
    );

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text('Change photo'), findsOneWidget);
    expect(find.text('Open camera'), findsOneWidget);
    expect(find.text('Open gallery'), findsOneWidget);

    await tester.tap(find.byKey(const Key('profile-picture-camera')));
    await tester.pumpAndSettle();

    expect(source, ImageSource.camera);
  });
}
