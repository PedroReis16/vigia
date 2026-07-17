import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/domain/enums/sheet_stages.dart';

class AppBarConfig {
  final String title;
  final bool showBackButton;
  final bool showFilterButton;

  const AppBarConfig({
    required this.title,
    this.showBackButton = false,
    this.showFilterButton = false,
  });

  factory AppBarConfig.fromState(GoRouterState state) {
    final option = state.pathParameters['option'];
    final id = state.pathParameters['id'];
    final stageName = state.pathParameters['stage'];

    final title = switch (state.matchedLocation) {
      AppRoutes.home => 'Home',
      AppRoutes.settings => 'Settings',
      _ when stageName != null => _stageTitle(stageName),
      _ when option != null => Uri.decodeComponent(option),
      _ when id != null => 'Ficha #$id',
      _ => 'Ceramics Planner',
    };
    const rootRoutes = {AppRoutes.home, AppRoutes.settings};
    final showBackButton = !rootRoutes.contains(state.matchedLocation);
    final showFilterButton = state.matchedLocation == AppRoutes.settings;
    return AppBarConfig(
      title: title,
      showBackButton: showBackButton,
      showFilterButton: showFilterButton,
    );
  }

  static String _stageTitle(String stageName) {
    try {
      return SheetStage.values.byName(stageName).label;
    } on ArgumentError {
      return 'Etapa';
    }
  }
}
