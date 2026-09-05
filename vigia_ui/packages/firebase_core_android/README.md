# firebase_core (Android-only)

Local override of `firebase_core` used by `vigia_ui` so iOS builds do not
link the Firebase iOS SDK / Swift packages.

Based on `firebase_core` 4.13.0 with Darwin/web/windows plugin platforms removed.
Update by copying `lib/` + `android/` from the matching pub.dev version and
keeping only the Android platform entry in `pubspec.yaml`.
