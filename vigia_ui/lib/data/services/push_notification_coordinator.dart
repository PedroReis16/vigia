import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:vigia_ui/core/app_routes.dart';
import 'package:vigia_ui/core/providers/repository_providers/push_token_repository_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

const androidFallAlertChannelId = 'vigia_fall_alerts';

const _androidFallAlertChannel = AndroidNotificationChannel(
  androidFallAlertChannelId,
  'Alertas de queda',
  description: 'Notificações quando uma queda é detectada',
  importance: Importance.high,
);

final FlutterLocalNotificationsPlugin _localNotifications =
    FlutterLocalNotificationsPlugin();

GoRouter? _notificationRouter;

/// Background FCM handler (must be top-level).
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

Future<void> initializeLocalNotifications() async {
  const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
  const darwinSettings = DarwinInitializationSettings(
    requestAlertPermission: false,
    requestBadgePermission: false,
    requestSoundPermission: false,
  );

  await _localNotifications.initialize(
    settings: const InitializationSettings(
      android: androidSettings,
      iOS: darwinSettings,
    ),
    onDidReceiveNotificationResponse: (response) {
      final payload = response.payload;
      if (payload == null || payload.isEmpty) return;
      final router = _notificationRouter;
      if (router == null) return;

      final decoded = jsonDecode(payload);
      if (decoded is Map<String, dynamic>) {
        _navigateToFallAlert(router, decoded);
      }
    },
  );

  await _localNotifications
      .resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin
      >()
      ?.createNotificationChannel(_androidFallAlertChannel);
}

void _navigateToFallAlert(GoRouter router, Map<String, dynamic> data) {
  if (data['type'] != 'fall') return;

  final deviceId = data['deviceId']?.toString();
  if (deviceId == null || deviceId.isEmpty) return;

  router.go('${AppRoutes.devicesPage}/$deviceId');
}

class PushNotificationCoordinator {
  PushNotificationCoordinator(this._ref);

  final Ref _ref;
  StreamSubscription<String>? _tokenRefreshSub;
  StreamSubscription<RemoteMessage>? _foregroundMessageSub;
  String? _currentToken;
  bool _initialized = false;

  Future<void> initialize(GoRouter router) async {
    if (_initialized) return;
    _initialized = true;
    _notificationRouter = router;

    if (Firebase.apps.isEmpty) {
      debugPrint('Push notifications skipped: Firebase is not initialized.');
      return;
    }

    await FirebaseMessaging.instance
        .setForegroundNotificationPresentationOptions(
          alert: true,
          badge: true,
          sound: true,
        );

    await _requestPermission();
    await _syncTokenIfAuthenticated();

    _tokenRefreshSub = FirebaseMessaging.instance.onTokenRefresh.listen((
      token,
    ) async {
      _currentToken = token;
      await _registerToken(token);
    });

    _foregroundMessageSub = FirebaseMessaging.onMessage.listen(
      _displayForegroundNotification,
    );

    FirebaseMessaging.onMessageOpenedApp.listen((message) {
      _navigateToFallAlert(router, message.data);
    });

    final initialMessage = await FirebaseMessaging.instance.getInitialMessage();
    if (initialMessage != null) {
      _navigateToFallAlert(router, initialMessage.data);
    }

    _ref.listen<AsyncValue<bool>>(authSessionProvider, (previous, next) {
      final wasAuthenticated = previous?.asData?.value ?? false;
      final isAuthenticated = next.asData?.value ?? false;

      if (!wasAuthenticated && isAuthenticated) {
        unawaited(_syncTokenIfAuthenticated());
      } else if (wasAuthenticated && !isAuthenticated) {
        _currentToken = null;
      }
    });
  }

  Future<void> syncAfterLogin() => _syncTokenIfAuthenticated();

  Future<void> unregisterCurrentToken() async {
    final token = _currentToken;
    if (token == null || token.isEmpty) return;

    try {
      await _ref.read(pushTokenRepositoryProvider).deleteToken(token);
    } catch (error, stackTrace) {
      debugPrint('Failed to delete push token: $error\n$stackTrace');
    } finally {
      _currentToken = null;
    }
  }

  Future<void> _requestPermission() async {
    try {
      final settings = await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
      debugPrint(
        'Push permission status: ${settings.authorizationStatus}',
      );
    } catch (error, stackTrace) {
      debugPrint('Push permission request failed: $error\n$stackTrace');
    }
  }

  Future<void> _syncTokenIfAuthenticated() async {
    final authenticated = _ref.read(authSessionProvider).asData?.value ?? false;
    if (!authenticated) return;

    try {
      if (Platform.isIOS) {
        final apnsToken = await _waitForApnsToken();
        if (apnsToken == null) {
          debugPrint(
            'Push token skipped: APNs token is not available. '
            'On iOS this usually means the Push Notifications capability is '
            'missing, APNs is not configured in Firebase, or the app is '
            'running on the Simulator.',
          );
          return;
        }
      }

      final token = await FirebaseMessaging.instance.getToken();
      if (token == null || token.isEmpty) {
        debugPrint('Push token skipped: FCM token is empty.');
        return;
      }
      _currentToken = token;
      debugPrint('FCM token acquired, registering with API.');
      await _registerToken(token);
    } catch (error, stackTrace) {
      debugPrint('Failed to sync push token: $error\n$stackTrace');
    }
  }

  Future<String?> _waitForApnsToken() async {
    for (var attempt = 0; attempt < 10; attempt++) {
      final token = await FirebaseMessaging.instance.getAPNSToken();
      if (token != null && token.isNotEmpty) return token;
      await Future<void>.delayed(const Duration(milliseconds: 500));
    }
    return FirebaseMessaging.instance.getAPNSToken();
  }

  Future<void> _registerToken(String token) async {
    final authenticated = _ref.read(authSessionProvider).asData?.value ?? false;
    if (!authenticated) return;

    final platform = Platform.isIOS ? 'ios' : 'android';

    try {
      await _ref.read(pushTokenRepositoryProvider).upsertToken(token, platform);
      debugPrint('FCM token registered ($platform).');
    } catch (error, stackTrace) {
      debugPrint('Failed to register push token: $error\n$stackTrace');
    }
  }

  Future<void> _displayForegroundNotification(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;

    // iOS already presents the system banner via
    // setForegroundNotificationPresentationOptions.
    if (Platform.isIOS) return;

    await _localNotifications.show(
      id: notification.hashCode,
      title: notification.title,
      body: notification.body,
      notificationDetails: NotificationDetails(
        android: AndroidNotificationDetails(
          _androidFallAlertChannel.id,
          _androidFallAlertChannel.name,
          channelDescription: _androidFallAlertChannel.description,
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
      payload: jsonEncode(message.data),
    );
  }

  void dispose() {
    _tokenRefreshSub?.cancel();
    _foregroundMessageSub?.cancel();
  }
}
