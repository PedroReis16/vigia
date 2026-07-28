import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/enums/sheet_stages.dart';

class AppBarConfig {
  final String title;
  final bool showAppBar;

  const AppBarConfig({required this.title, this.showAppBar = true});

  factory AppBarConfig.fromState(GoRouterState state) {
    final option = state.pathParameters['option'];
    final id = state.pathParameters['id'];
    final stageName = state.pathParameters['stage'];

    final title = switch (state.matchedLocation) {
      AppRoutes.devicesPage => 'Dispositivos',
      AppRoutes.settingsPage => 'Configurações',
      _ when stageName != null => _stageTitle(stageName),
      _ when option != null => Uri.decodeComponent(option),
      _ when id != null => 'Ficha #$id',
      _ => 'Ceramics Planner',
    };

    final showBar = !state.pathParameters.keys.contains('deviceId');

    return AppBarConfig(title: title, showAppBar: showBar);
  }

  static String _stageTitle(String stageName) {
    try {
      return SheetStage.values.byName(stageName).label;
    } on ArgumentError {
      return 'Etapa';
    }
  }
}
