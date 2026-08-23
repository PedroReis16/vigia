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

/// Push is Android-only: iPhone (simulator or device) must not init FCM/APNs.
bool get arePushNotificationsEnabled => Platform.isAndroid;

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

  await _localNotifications.initialize(
    settings: const InitializationSettings(android: androidSettings),
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

    if (!arePushNotificationsEnabled) {
      debugPrint('Push notifications skipped: Android only.');
      return;
    }

    if (Firebase.apps.isEmpty) {
      debugPrint('Push notifications skipped: Firebase is not initialized.');
      return;
    }

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
    if (!arePushNotificationsEnabled) return;

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
      debugPrint('Push permission status: ${settings.authorizationStatus}');
    } catch (error, stackTrace) {
      debugPrint('Push permission request failed: $error\n$stackTrace');
    }
  }

  Future<void> _syncTokenIfAuthenticated() async {
    if (!arePushNotificationsEnabled) return;

    final authenticated = _ref.read(authSessionProvider).asData?.value ?? false;
    if (!authenticated) return;

    try {
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

  Future<void> _registerToken(String token) async {
    final authenticated = _ref.read(authSessionProvider).asData?.value ?? false;
    if (!authenticated) return;

    try {
      await _ref
          .read(pushTokenRepositoryProvider)
          .upsertToken(token, 'android');
      debugPrint('FCM token registered (android).');
    } catch (error, stackTrace) {
      debugPrint('Failed to register push token: $error\n$stackTrace');
    }
  }

  Future<void> _displayForegroundNotification(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;

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
