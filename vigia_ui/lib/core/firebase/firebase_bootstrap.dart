import 'firebase_bootstrap_stub.dart'
    if (dart.library.io) 'firebase_bootstrap_io.dart' as impl;

/// Initializes Firebase/FCM on Android only (runtime guard in IO bootstrap).
Future<void> initializeFirebaseForPushIfNeeded() =>
    impl.initializeFirebaseForPushIfNeeded();
