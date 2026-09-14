enum SheetStage { home, settings }

extension SheetStageLabels on SheetStage {
  String get label => switch (this) {
    SheetStage.home => 'Home',
    SheetStage.settings => 'Settings',
  };
}
