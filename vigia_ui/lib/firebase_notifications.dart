import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_in_app_messaging/firebase_in_app_messaging.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Canal Android compartilhado com FCM ([AndroidManifest] `default_notification_channel_id`).
const String _androidChannelId = 'vigia_notifications';
const String _androidChannelName = 'Notificações Vigia';
const String _androidChannelDescription = 'Alertas e mensagens do Vigia';

final FlutterLocalNotificationsPlugin _localNotifications =
    FlutterLocalNotificationsPlugin();

bool _initialized = false;

/// Chamado quando o utilizador abre a app a partir de uma notificação FCM.
void Function(RemoteMessage message)? onFcmNotificationOpened;

/// Chamado ao tocar numa notificação local (ex.: primeiro plano Android) ou cold start via payload.
void Function(String? payload)? onLocalNotificationPayload;

final FlutterLocalNotificationsPlugin localNotificationsPlugin =
    _localNotifications;

/// Handler em isolate separado (background / terminado).
/// Registar com [FirebaseMessaging.onBackgroundMessage] antes de [Firebase.initializeApp].
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();

  if (kDebugMode) {
    debugPrint(
      'FCM background: id=${message.messageId} '
      'notification=${message.notification != null} data=${message.data}',
    );
  }

  if (defaultTargetPlatform != TargetPlatform.android) {
    return;
  }

  // Com payload "notification", o Android mostra na bandeja sem Dart.
  if (message.notification != null) {
    return;
  }

  final display = _displayPayloadFromMessage(message);
  if (display == null) {
    return;
  }

  final plugin = FlutterLocalNotificationsPlugin();
  await plugin.initialize(
    settings: const InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
    ),
  );

  const channel = AndroidNotificationChannel(
    _androidChannelId,
    _androidChannelName,
    description: _androidChannelDescription,
    importance: Importance.high,
  );
  await plugin
      .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(channel);

  await plugin.show(
    id: notificationIdFrom(message),
    title: display.title,
    body: display.body,
    notificationDetails: NotificationDetails(
      android: AndroidNotificationDetails(
        _androidChannelId,
        _androidChannelName,
        channelDescription: _androidChannelDescription,
        importance: Importance.high,
        priority: Priority.high,
      ),
    ),
    payload: message.data.isEmpty ? null : message.data.toString(),
  );
}

/// Inicializa permissões, canais, listeners e cold start (FCM + notificação local).
Future<void> initializeFirebaseNotifications({
  void Function(RemoteMessage message)? onOpenedFromFcm,
  void Function(String? payload)? onOpenedFromLocal,
}) async {
  if (_initialized) {
    return;
  }
  _initialized = true;

  onFcmNotificationOpened = onOpenedFromFcm;
  onLocalNotificationPayload = onOpenedFromLocal;

  const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
  const darwinInit = DarwinInitializationSettings(
    requestAlertPermission: false,
    requestBadgePermission: false,
    requestSoundPermission: false,
  );
  const initSettings = InitializationSettings(
    android: androidInit,
    iOS: darwinInit,
    macOS: darwinInit,
  );

  await _localNotifications.initialize(
    settings: initSettings,
    onDidReceiveNotificationResponse: _onLocalNotificationTapped,
  );

  await _ensureAndroidChannel();

  final messaging = FirebaseMessaging.instance;

  await messaging.setForegroundNotificationPresentationOptions(
    alert: true,
    badge: true,
    sound: true,
  );

  final permission = await messaging.requestPermission(
    alert: true,
    announcement: false,
    badge: true,
    carPlay: false,
    criticalAlert: false,
    provisional: false,
    sound: true,
  );
  if (kDebugMode) {
    debugPrint('FCM permission: ${permission.authorizationStatus}');
  }

  FirebaseMessaging.onMessage.listen(_onForegroundMessage);
  FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationOpened);

  final initial = await messaging.getInitialMessage();
  if (initial != null) {
    _handleNotificationOpened(initial);
  }

  final launchDetails = await _localNotifications.getNotificationAppLaunchDetails();
  if (launchDetails?.didNotificationLaunchApp == true) {
    final payload = launchDetails!.notificationResponse?.payload;
    _dispatchLocalPayload(payload, reason: 'cold_start_local');
  }

  messaging.onTokenRefresh.listen((token) {
    if (kDebugMode) debugPrint('FCM token (refresh): $token');
  });

  final token = await messaging.getToken();
  if (kDebugMode) debugPrint('FCM token: $token');

  await FirebaseInAppMessaging.instance.setMessagesSuppressed(false);
}

Future<void> _ensureAndroidChannel() async {
  const channel = AndroidNotificationChannel(
    _androidChannelId,
    _androidChannelName,
    description: _androidChannelDescription,
    importance: Importance.high,
  );
  final android = _localNotifications.resolvePlatformSpecificImplementation<
      AndroidFlutterLocalNotificationsPlugin>();
  await android?.createNotificationChannel(channel);
}

void _onLocalNotificationTapped(NotificationResponse response) {
  _dispatchLocalPayload(response.payload, reason: 'tap_local');
}

void _dispatchLocalPayload(String? payload, {required String reason}) {
  if (kDebugMode) {
    debugPrint('Notificação local ($reason): payload=$payload');
  }
  onLocalNotificationPayload?.call(payload);
}

void _handleNotificationOpened(RemoteMessage message) {
  if (kDebugMode) {
    debugPrint(
      'Aberto via FCM: id=${message.messageId} data=${message.data}',
    );
  }
  onFcmNotificationOpened?.call(message);
}

Future<void> _onForegroundMessage(RemoteMessage message) async {
  final display = _displayPayloadFromMessage(message);
  if (display == null) {
    if (kDebugMode) {
      debugPrint(
        'FCM primeiro plano sem título/corpo utilizável; data=${message.data}',
      );
    }
    return;
  }

  final payload =
      message.data.isEmpty ? null : message.data.toString();

  switch (defaultTargetPlatform) {
    case TargetPlatform.android:
      await _localNotifications.show(
        id: notificationIdFrom(message),
        title: display.title,
        body: display.body,
        notificationDetails: NotificationDetails(
          android: AndroidNotificationDetails(
            _androidChannelId,
            _androidChannelName,
            channelDescription: _androidChannelDescription,
            importance: Importance.high,
            priority: Priority.high,
            icon: message.notification?.android?.smallIcon,
          ),
        ),
        payload: payload,
      );
    case TargetPlatform.iOS:
    case TargetPlatform.macOS:
      if (message.notification != null) {
        // Banner/som via [setForegroundNotificationPresentationOptions].
        return;
      }
      await _localNotifications.show(
        id: notificationIdFrom(message),
        title: display.title,
        body: display.body,
        notificationDetails: NotificationDetails(
          iOS: const DarwinNotificationDetails(
            presentAlert: true,
            presentBanner: true,
            presentSound: true,
            presentBadge: true,
          ),
          macOS: const DarwinNotificationDetails(
            presentAlert: true,
            presentBanner: true,
            presentSound: true,
            presentBadge: true,
          ),
        ),
        payload: payload,
      );
    default:
      break;
  }
}

/// Título/corpo a partir do payload [notification] ou das chaves habituais em [data].
_DisplayPayload? _displayPayloadFromMessage(RemoteMessage message) {
  final n = message.notification;
  var title = n?.title?.trim();
  var body = n?.body?.trim();
  final d = message.data;

  title ??= _firstNonEmptyString([
    d['title'],
    d['notification_title'],
    d['gcm.notification.title'],
    d['titulo'],
  ]);
  body ??= _firstNonEmptyString([
    d['body'],
    d['message'],
    d['notification_body'],
    d['gcm.notification.body'],
    d['mensagem'],
  ]);

  if ((title == null || title.isEmpty) && (body == null || body.isEmpty)) {
    return null;
  }
  return _DisplayPayload(title: title, body: body);
}

String? _firstNonEmptyString(List<dynamic> values) {
  for (final v in values) {
    if (v is String && v.trim().isNotEmpty) return v.trim();
  }
  return null;
}

class _DisplayPayload {
  const _DisplayPayload({required this.title, required this.body});

  final String? title;
  final String? body;
}

/// ID estável e positivo para o canal local / [`AndroidNotificationDetails`].
int notificationIdFrom(RemoteMessage message) {
  final raw = message.messageId?.hashCode ??
      Object.hash(
        message.notification?.title,
        message.notification?.body,
        message.data.toString(),
      );
  return raw.abs() % 0x7FFFFFFF;
}
