import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/presentation/settings/widgets/settings_section.dart';
import 'package:vigia_ui/presentation/settings/widgets/settings_tile.dart';

void main() {
  group('SettingsTile', () {
    testWidgets('renders title, subtitle, and chevron when tappable', (
      tester,
    ) async {
      var tapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SettingsTile(
              icon: Icons.settings,
              title: 'Account',
              subtitle: 'Manage profile',
              onTap: () => tapped = true,
            ),
          ),
        ),
      );

      expect(find.text('Account'), findsOneWidget);
      expect(find.text('Manage profile'), findsOneWidget);
      expect(find.byIcon(Icons.chevron_right_rounded), findsOneWidget);

      await tester.tap(find.text('Account'));
      expect(tapped, isTrue);
    });

    testWidgets('shows custom trailing instead of chevron', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: SettingsTile(
              icon: Icons.logout,
              title: 'Sign out',
              trailing: Icon(Icons.exit_to_app),
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.exit_to_app), findsOneWidget);
      expect(find.byIcon(Icons.chevron_right_rounded), findsNothing);
    });
  });

  group('SettingsSection', () {
    testWidgets('renders section title and children with dividers', (
      tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SettingsSection(
              title: 'Preferences',
              children: const [
                SettingsTile(icon: Icons.language, title: 'Language'),
                SettingsTile(icon: Icons.dark_mode, title: 'Theme'),
              ],
            ),
          ),
        ),
      );

      expect(find.text('Preferences'), findsOneWidget);
      expect(find.text('Language'), findsOneWidget);
      expect(find.text('Theme'), findsOneWidget);
      expect(find.byType(Divider), findsOneWidget);
    });
  });
}
