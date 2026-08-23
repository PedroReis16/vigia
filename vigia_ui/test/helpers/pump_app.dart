import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/theme/app_theme.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';

/// Shared localizations + locale for widget tests.
List<LocalizationsDelegate<dynamic>> get testLocalizationDelegates =>
    AppLocalizations.localizationsDelegates;

List<Locale> get testSupportedLocales => AppLocalizations.supportedLocales;

const testLocale = Locale('en');

/// Pumps [child] under [MaterialApp] with l10n and optional [ProviderScope] overrides.
Future<void> pumpApp(
  WidgetTester tester, {
  required Widget child,
  List<Override> overrides = const [],
  Locale locale = testLocale,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: overrides,
      child: MaterialApp(
        locale: locale,
        theme: AppTheme.light,
        localizationsDelegates: testLocalizationDelegates,
        supportedLocales: testSupportedLocales,
        home: child,
      ),
    ),
  );
}

/// Pumps a [GoRouter] under [UncontrolledProviderScope] with l10n.
Future<void> pumpRouterApp(
  WidgetTester tester, {
  required ProviderContainer container,
  required GoRouter router,
  Locale locale = testLocale,
}) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp.router(
        locale: locale,
        theme: AppTheme.light,
        localizationsDelegates: testLocalizationDelegates,
        supportedLocales: testSupportedLocales,
        routerConfig: router,
      ),
    ),
  );
}
