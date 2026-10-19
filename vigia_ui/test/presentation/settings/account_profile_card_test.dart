import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/user_profile.dart';
import 'package:vigia_ui/presentation/settings/widgets/account_profile_card.dart';

import '../../helpers/pump_app.dart';

void main() {
  const profile = UserProfile(
    id: 'user-1',
    name: 'Ana Lima',
    firstName: 'Ana',
    lastName: 'Lima',
    email: 'ana@vigia.test',
    phone: '11999990000',
    pictureUrl: 'https://example.test/picture.jpg',
  );

  Future<void> pumpCard(
    WidgetTester tester, {
    UserProfile current = profile,
    Future<bool> Function(String, String, String)? onSave,
    VoidCallback? onChangePicture,
    Future<bool> Function()? onRemovePicture,
    VoidCallback? onDeleteAccount,
  }) {
    return pumpApp(
      tester,
      child: SingleChildScrollView(
        child: AccountProfileCard(
          profile: current,
          onChangePicture: onChangePicture ?? () {},
          onRemovePicture: onRemovePicture ?? () async => true,
          onSave: onSave ?? (_, _, _) async => true,
          onDeleteAccount: onDeleteAccount ?? () {},
        ),
      ),
    );
  }

  testWidgets('shows profile fields and hides photo actions until edit', (
    tester,
  ) async {
    var changed = false;

    await pumpCard(
      tester,
      onChangePicture: () => changed = true,
      onRemovePicture: () async {
        fail('removal must wait for save');
      },
    );

    expect(find.text('Profile'), findsOneWidget);
    expect(
      tester.widget<Text>(find.text('Profile')).style?.fontWeight,
      FontWeight.w700,
    );
    expect(find.text('Ana Lima'), findsOneWidget);
    expect(find.text('Ana'), findsOneWidget);
    expect(find.text('Lima'), findsOneWidget);
    expect(find.text('ana@vigia.test'), findsOneWidget);
    expect(find.text('11999990000'), findsOneWidget);
    expect(find.text('Delete account'), findsNWidgets(2));
    expect(find.text('Remove photo'), findsNothing);
    expect(find.byKey(const Key('profile-picture-button')), findsNothing);

    await tester.tap(find.byKey(const Key('profile-edit')));
    await tester.pump();

    expect(find.text('Remove photo'), findsOneWidget);
    expect(find.byIcon(Icons.photo_camera_outlined), findsOneWidget);

    await tester.tap(find.byKey(const Key('profile-picture-button')));
    await tester.tap(find.text('Remove photo'));
    await tester.pump();

    expect(changed, isTrue);
    expect(find.text('Remove photo'), findsNothing);
    expect(find.text('AL'), findsOneWidget);
  });

  testWidgets('removes the photo only after save', (tester) async {
    var removed = false;

    await pumpCard(
      tester,
      onRemovePicture: () async {
        removed = true;
        return true;
      },
    );

    await tester.tap(find.byKey(const Key('profile-edit')));
    await tester.pump();
    await tester.tap(find.text('Remove photo'));
    await tester.pump();

    expect(removed, isFalse);

    final save = find.byKey(const Key('profile-save'));
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pump();

    expect(removed, isTrue);
    expect(find.byKey(const Key('profile-edit')), findsOneWidget);
  });

  testWidgets('saves a changed name and leaves edit mode', (tester) async {
    String? savedFirst;

    await pumpCard(
      tester,
      onSave: (first, _, _) async {
        savedFirst = first;
        return true;
      },
    );

    await tester.tap(find.byKey(const Key('profile-edit')));
    await tester.pump();

    final save = find.byKey(const Key('profile-save'));
    expect(tester.widget<FilledButton>(save).onPressed, isNull);

    await tester.enterText(
      find.byKey(const Key('profile-first-name')),
      'Maria',
    );
    await tester.pump();
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pump();

    expect(savedFirst, 'Maria');
    expect(find.byKey(const Key('profile-edit')), findsOneWidget);
  });

  testWidgets(
    'uses initials and hides delete when the account cannot be removed',
    (tester) async {
      await pumpCard(
        tester,
        current: const UserProfile(
          id: 'user-2',
          name: 'ana@vigia.test',
          firstName: '',
          lastName: '',
          email: 'ana@vigia.test',
          phone: '',
          canDeleteAccount: false,
        ),
      );

      expect(find.text('AN'), findsOneWidget);
      expect(find.text('—'), findsNWidgets(3));
      expect(find.text('Delete account'), findsNothing);

      await tester.tap(find.byKey(const Key('profile-edit')));
      await tester.pump();

      expect(find.text('Remove photo'), findsNothing);
    },
  );
}
