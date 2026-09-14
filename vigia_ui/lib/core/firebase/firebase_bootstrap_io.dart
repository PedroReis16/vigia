import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:vigia_ui/data/services/push_notification_coordinator.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

Future<void> initializeFirebaseForPushIfNeeded() async {
  if (!Platform.isAndroid) return;

  try {
    // Android reads credentials from android/app/google-services.json.
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
    await initializeLocalNotifications();
  } catch (error, stackTrace) {
    debugPrint('Firebase initialization skipped: $error\n$stackTrace');
  }
}
