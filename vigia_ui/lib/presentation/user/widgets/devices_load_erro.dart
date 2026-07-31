import 'package:flutter/material.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class DevicesLoadError extends StatelessWidget {
  const DevicesLoadError({super.key, required this.onTryAgain});

  final Function() onTryAgain;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          height: MediaQuery.sizeOf(context).height * 0.3,
          width: MediaQuery.sizeOf(context).width * 0.8,
          child: Image.asset('assets/images/device_load_error.png'),
        ),
        Padding(
          padding: EdgeInsets.all(16),
          child: Text(
            context.translations.devicesLoadError,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
        TextButton(
          onPressed: onTryAgain,
          style: const ButtonStyle(
            splashFactory: NoSplash.splashFactory,
          ),
          child: Text(context.translations.tryAgain),
        ),
      ],
    );
  }
}
