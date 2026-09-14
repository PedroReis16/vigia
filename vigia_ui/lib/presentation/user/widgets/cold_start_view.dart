import 'package:flutter/material.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';

/// Full-bleed primary surface with the Vigia logo centered.
///
/// Used as the app cold-start frame before resolving auth session.
class ColdStartView extends StatelessWidget {
  const ColdStartView({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Material(
        type: MaterialType.transparency,
        child: VigiaLogoHero.image(height: VigiaLogoHero.authHeight),
      ),
    );
  }
}
