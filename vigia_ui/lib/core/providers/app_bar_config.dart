import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/enums/sheet_stages.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class AppBarConfig {
  final String title;
  final bool showAppBar;

  const AppBarConfig({required this.title, this.showAppBar = true});

  factory AppBarConfig.fromState(BuildContext context, GoRouterState state) {
    final option = state.pathParameters['option'];
    final id = state.pathParameters['id'];
    final stageName = state.pathParameters['stage'];

    final title = switch (state.matchedLocation) {
      AppRoutes.devicesPage => context.translations.devices,
      AppRoutes.settingsPage => context.translations.settings,
      _ when stageName != null => _stageTitle(context.translations, stageName),
      _ when option != null => Uri.decodeComponent(option),
      _ when id != null => context.translations.sheetRecord(id),
      _ => context.translations.appTitle,
    };

    final showBar = !state.pathParameters.keys.contains('deviceId');

    return AppBarConfig(title: title, showAppBar: showBar);
  }

  static String _stageTitle(AppLocalizations l10n, String stageName) {
    try {
      return switch (SheetStage.values.byName(stageName)) {
        SheetStage.home => l10n.home,
        SheetStage.settings => l10n.settings,
      };
    } on ArgumentError {
      return l10n.stage;
    }
  }
}
