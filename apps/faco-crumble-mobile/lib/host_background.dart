import 'dart:async';
import 'dart:typed_data';
import 'dart:ui';
import 'package:flutter/services.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_background_service_android/flutter_background_service_android.dart';
import 'package:flutter/widgets.dart';
import 'crumble_server.dart';

/// Runs the actual HTTP/WebSocket server on the Android foreground-service
/// FlutterEngine, not the visible Activity isolate. No session survives a
/// deliberate stop, and no credentials are saved to disk.
@pragma('vm:entry-point')
void facoHostBackground(ServiceInstance service) async {
  WidgetsFlutterBinding.ensureInitialized();
  DartPluginRegistrant.ensureInitialized();
  CrumbleServer? current;
  bool launching = false;
  bool stopping = false;
  StreamSubscription? events;
  Timer? heartbeat;

  Future<Uint8List> asset(String name) async {
    final data = await rootBundle.load('assets/web/$name');
    return data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
  }

  void snapshot() {
    if (current == null || !current!.isRunning) {
      service.invoke('session.state', {'running': false});
      return;
    }
    service.invoke('session.state', {'running': true, ...current!.snapshot()});
  }

  service.on('session.start').listen((arg) async {
    if (stopping || launching) return;
    if (current?.isRunning == true) { snapshot(); return; }
    launching = true;
    final count = arg?['count'] is int ? arg!['count'] as int : 10;
    final requested = count.clamp(1, 10);
    final created = CrumbleServer(assetLoader: asset);
    try {
      await created.start(participantCount: requested);
      if (stopping) { await created.stop(); return; }
      current = created;
      await events?.cancel();
      events = created.events.listen((event) {
        if (event['type'] == 'presence' || event['type'] == 'rotated' || event['type'] == 'url') snapshot();
      });
      heartbeat?.cancel();
      heartbeat = Timer.periodic(const Duration(seconds: 3), (_) => snapshot());
      snapshot();
    } catch (e) {
      await created.stop();
      if (!stopping) service.invoke('session.error', {'message': 'Could not start phone server: $e'});
    } finally {
      launching = false;
    }
  });
  service.on('session.setBase').listen((arg) {
    try {
      if (current?.isRunning != true) return;
      final url = arg?['url']?.toString() ?? '';
      current!.setPublicUrl(url, reconnected: arg?['reconnected'] == true);
      snapshot();
    } catch (e) {
      service.invoke('session.error', {'message': e.toString()});
    }
  });
  service.on('session.rotate').listen((_) {
    if (current?.isRunning == true) {
      current!.rotate(); snapshot();
    }
  });
  service.on('session.snapshot').listen((_) => snapshot());
  service.on('session.stop').listen((_) async {
    stopping = true;
    heartbeat?.cancel();
    await events?.cancel();
    await current?.stop();
    current = null;
    snapshot();
    service.stopSelf();
  });
  snapshot();
}

Future<void> configureHostBackground() async {
  final service = FlutterBackgroundService();
  await service.configure(
    iosConfiguration: IosConfiguration(autoStart: false, onForeground: facoHostBackground),
    androidConfiguration: AndroidConfiguration(
      onStart: facoHostBackground,
      autoStart: false,
      autoStartOnBoot: false,
      isForegroundMode: true,
      initialNotificationTitle: 'FACO Crumble · Session active',
      initialNotificationContent: 'This phone is hosting an invitation-only conversation',
      foregroundServiceNotificationId: 7787,
      foregroundServiceTypes: [AndroidForegroundType.connectedDevice],
    ),
  );
}
