import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/user_profile.dart';
import 'package:vigia_ui/presentation/settings/providers/user_profile_provider.dart';
import 'package:vigia_ui/presentation/shared/widgets/menu_component.dart';

import '../../helpers/pump_app.dart';

class _FixedProfile extends UserProfileController {
  _FixedProfile(this.profile);

  final UserProfile profile;

  @override
  Future<UserProfile> build() async => profile;
}

void main() {
  testWidgets('uses initials in the profile slot when there is no photo', (
    tester,
  ) async {
    var index = -1;

    await pumpApp(
      tester,
      overrides: [
        userProfileProvider.overrideWith(
          () => _FixedProfile(
            const UserProfile(
              id: 'user-1',
              name: 'Ana Lima',
              firstName: 'Ana',
              lastName: 'Lima',
              email: 'ana@vigia.test',
              phone: '11999990000',
            ),
          ),
        ),
      ],
      child: MenuComponent(
        currentIndex: 1,
        onItemTap: (value) => index = value,
      ),
    );
    await tester.pump();

    expect(find.byIcon(Icons.settings), findsNothing);
    expect(find.text('AL'), findsOneWidget);

    await tester.tap(find.byKey(const Key('nav-profile-avatar')));
    expect(index, 1);
  });
}
