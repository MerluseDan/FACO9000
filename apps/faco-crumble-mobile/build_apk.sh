#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v flutter >/dev/null 2>&1; then
  echo 'Flutter SDK is not installed. Use GitHub Actions (android-apk.yml) or install Flutter first.' >&2
  exit 1
fi
flutter pub get
flutter create --platforms=android --org com.faco --project-name faco_crumble_mobile .
python3 tool/configure_android.py
dart run flutter_launcher_icons
rm -f test/widget_test.dart
flutter test
flutter build apk --debug --target-platform android-arm64
printf '\nFACO APK: %s\n' "$(pwd)/build/app/outputs/flutter-apk/app-debug.apk"
sha256sum build/app/outputs/flutter-apk/app-debug.apk
