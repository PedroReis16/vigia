# firebase_messaging (Android-only)

Local override of `firebase_messaging` used by `vigia_ui` so iOS builds do not
link the Firebase iOS SDK / Swift packages.

Based on `firebase_messaging` 16.5.0 with Darwin/web plugin platforms removed.
Update by copying `lib/` + `android/` from the matching pub.dev version and
keeping only the Android platform entry in `pubspec.yaml`.
