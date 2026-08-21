import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/core/app_router.dart';
import 'package:vigia_ui/core/deep_link_listener.dart';
import 'package:vigia_ui/core/providers/push_notification_provider.dart';
import 'package:vigia_ui/data/services/push_notification_coordinator.dart';
import 'package:vigia_ui/firebase_options.dart';
import 'package:vigia_ui/presentation/devices/providers/device_groups_realtime_provider.dart';
import 'package:vigia_ui/core/theme/app_theme.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shell/auth_transition_warm_up.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  String envFile = "";
  if (kDebugMode) {
    envFile = "homolog.env";
  } else {
    envFile = ".env";
  }

  await dotenv.load(fileName: envFile);

  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
    await initializeLocalNotifications();
  } catch (error, stackTrace) {
    debugPrint('Firebase initialization skipped: $error\n$stackTrace');
  }

  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(ProviderScope(retry: (retryCount, error) => null, child: MyApp()));
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    // Keep SignalR bridge alive for the whole app session.
    ref.watch(deviceGroupsRealtimeBridgeProvider);

    final pushCoordinator = ref.read(pushNotificationCoordinatorProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      pushCoordinator.initialize(router);
    });

    return MaterialApp.router(
      onGenerateTitle: (context) => context.translations.appTitle,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.light,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      localeResolutionCallback: (locale, supportedLocales) {
        if (locale != null) {
          for (final supported in supportedLocales) {
            if (supported.languageCode == locale.languageCode) {
              return supported;
            }
          }
        }
        return supportedLocales.first;
      },
      routerConfig: router,
      builder: (context, child) {
        // Context below MaterialApp has MediaQuery — safe for ResizeImage DPR.
        WidgetsBinding.instance.addPostFrameCallback((_) {
          AuthTransitionWarmUp.precacheLogos(context);
        });
        return DeepLinkListener(child: child ?? const SizedBox.shrink());
      },
    );
  }
}
