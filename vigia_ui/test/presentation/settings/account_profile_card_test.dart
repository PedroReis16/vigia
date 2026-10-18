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

  testWidgets('shows name, email, phone and picture actions', (tester) async {
    var changed = false;
    var removed = false;

    await pumpApp(
      tester,
      child: AccountProfileCard(
        profile: profile,
        onChangePicture: () => changed = true,
        onRemovePicture: () => removed = true,
      ),
    );

    expect(find.text('Ana Lima'), findsOneWidget);
    expect(find.text('ana@vigia.test'), findsOneWidget);
    expect(find.text('11999990000'), findsOneWidget);
    expect(find.text('Change photo'), findsOneWidget);
    expect(find.text('Remove photo'), findsOneWidget);

    await tester.tap(find.text('Change photo'));
    await tester.tap(find.text('Remove photo'));

    expect(changed, isTrue);
    expect(removed, isTrue);
  });

  testWidgets('uses initials and hides remove when there is no photo', (
    tester,
  ) async {
    await pumpApp(
      tester,
      child: AccountProfileCard(
        profile: const UserProfile(
          id: 'user-2',
          name: 'ana@vigia.test',
          firstName: '',
          lastName: '',
          email: 'ana@vigia.test',
          phone: '',
        ),
        onChangePicture: () {},
        onRemovePicture: () {},
      ),
    );

    expect(find.text('AN'), findsOneWidget);
    expect(find.text('—'), findsOneWidget);
    expect(find.text('Remove photo'), findsNothing);
  });
}
