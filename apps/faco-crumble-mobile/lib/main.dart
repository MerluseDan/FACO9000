import 'dart:async';
import 'dart:io';
import 'dart:math' as math;
import 'package:cloudflared_tunnel/cloudflared_tunnel.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
import 'host_background.dart';

const Color facoBlue = Color(0xFF2369E8);
const Color facoInk = Color(0xFF18304D);
const Color facoMist = Color(0xFFF1F6FD);
const Color facoSoft = Color(0xFF6D8098);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (Platform.isAndroid) await configureHostBackground();
  runApp(const CrumbleApp());
}

class CrumbleApp extends StatelessWidget {
  const CrumbleApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'FACO Crumble',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      useMaterial3: true, colorScheme: ColorScheme.fromSeed(seedColor: facoBlue, surface: Colors.white),
      scaffoldBackgroundColor: facoMist,
      inputDecorationTheme: InputDecorationTheme(
        filled: true, fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Color(0xFFDCE7F5))),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      ),
    ),
    home: const CrumbleHome(),
  );
}

class CrumbleHome extends StatefulWidget {
  const CrumbleHome({super.key});
  @override
  State<CrumbleHome> createState() => _CrumbleHomeState();
}

class _CrumbleHomeState extends State<CrumbleHome> with TickerProviderStateMixin {
  final _tokenInput = TextEditingController();
  final _domainInput = TextEditingController();
  final _service = FlutterBackgroundService();
  final _cloudflare = CloudflaredTunnel();
  late final AnimationController _infinity = AnimationController(vsync: this, duration: const Duration(seconds: 3));
  StreamSubscription? _sessionStream;
  StreamSubscription? _errorStream;
  StreamSubscription? _tunnelStream;
  StreamSubscription? _tunnelErrors;
  Map<String, dynamic> _state = {'running': false};
  String _alert = '';
  String _tunnelState = 'Not connected';
  String _localAddress = '';
  bool _starting = false;
  bool _internet = true;
  bool _tunnelConnected = false;
  bool _hadTunnelConnection = false;
  bool _reducedMotion = false;
  int _participantCount = 10;
  int _selectedQR = 1;
  int _phase = 0; // 0 = choose, 1 = host setup, 2 = host running

  bool get _running => _state['running'] == true;
  int get _online => (_state['online'] as num?)?.toInt() ?? 0;
  int get _activeCalls => (_state['activeCalls'] as num?)?.toInt() ?? 0;
  List<Map<String, dynamic>> get _invites => (_state['invites'] as List?)?.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList() ?? [];

  @override
  void initState() {
    super.initState();
    _sessionStream = _service.on('session.state').listen((event) {
      if (!mounted || event == null) return;
      setState(() {
        _state = Map<String, dynamic>.from(event);
        if (_running) _phase = 2;
        _syncInfinity();
      });
    });
    _errorStream = _service.on('session.error').listen((event) {
      if (mounted) _warn(event?['message']?.toString() ?? 'Phone server error');
    });
    _tunnelStream = _cloudflare.tunnelStateStream.listen((state) {
      if (!mounted) return;
      final label = state.name;
      final connected = label == 'connected';
      final reconnected = connected && !_tunnelConnected && _hadTunnelConnection;
      setState(() { _tunnelState = label; _tunnelConnected = connected; });
      if (connected && _running && _internet) {
        final url = _domainInput.text.trim();
        _service.invoke('session.setBase', {'url': url, 'reconnected': reconnected});
        _hadTunnelConnection = true;
      }
      if (label == 'disconnected' || label == 'reconnecting' || label == 'error') {
        // Remember earlier connection; next transition back to connected rotates.
        // Do not share stale invitations during network outages.
      }
    });
    _tunnelErrors = _cloudflare.tunnelErrorStream.listen((message) { if (mounted) _warn('Cloudflare: $message'); });
    _restoreIfAlreadyHosting();
  }

  void _syncInfinity() {
    if (_activeCalls > 0 && !_reducedMotion) {
      if (!_infinity.isAnimating) _infinity.repeat();
    } else {
      _infinity.stop(); _infinity.value = 0;
    }
  }

  Future<void> _restoreIfAlreadyHosting() async {
    if (await _service.isRunning()) _service.invoke('session.snapshot');
  }

  void _warn(String msg) {
    if (!mounted) return;
    setState(() => _alert = msg);
  }

  Future<void> _host() async {
    if (_starting || _running) return;
    if (_internet) {
      final u = Uri.tryParse(_domainInput.text.trim());
      if (u == null || u.scheme != 'https' || u.host.isEmpty || u.userInfo.isNotEmpty ||
          (u.path.isNotEmpty && u.path != '/') || u.hasQuery || u.hasFragment) {
        _warn('Enter your Cloudflare public HTTPS hostname, e.g. https://talk.example.com');
        return;
      }
      if (_tokenInput.text.trim().isEmpty) {
        _warn('Enter the Cloudflare tunnel token. It is kept in memory only.');
        return;
      }
    }
    setState(() { _starting = true; _alert = ''; });
    try {
      final readyEvent = _service.on('session.state')
          .where((s) => s?['running'] == true).first.timeout(const Duration(seconds: 15));
      final started = await _service.startService();
      if (!started) throw StateError('Android foreground hosting service could not start.');
      // Retry only the idempotent start IPC until the background FlutterEngine
      // has attached its listeners. UI listeners were installed before start.
      _service.invoke('session.start', {'count': _participantCount});
      final attemptTimer = Timer.periodic(const Duration(milliseconds: 700), (_) {
        _service.invoke('session.start', {'count': _participantCount});
      });
      Map<String, dynamic>? ready;
      try { ready = await readyEvent; } finally { attemptTimer.cancel(); }
      if (ready == null) throw StateError('No server readiness response.');
      if (_internet) {
        if (!await _cloudflare.hasNotificationPermission()) {
          await _cloudflare.requestNotificationPermission();
        }
        await _cloudflare.startTunnel(
          token: _tokenInput.text.trim(),
          originUrl: 'http://127.0.0.1:8787',
        );
        _tokenInput.clear();
        _tunnelState = 'Connecting';
        if (_tunnelConnected) {
          _service.invoke('session.setBase', {'url': _domainInput.text.trim(), 'reconnected': false});
        }
        // The stream will mark readiness and issue the correct base URL.
      } else {
        await _detectLanIp();
      }
      if (!mounted) return;
      setState(() { _phase = 2; _selectedQR = 1; });
    } catch (e) {
      _warn('Hosting could not start: $e');
      if (_internet) { try { await _cloudflare.stopTunnel(); } catch (_) {} }
      _service.invoke('session.stop');
    } finally {
      if (mounted) setState(() => _starting = false);
    }
  }

  Future<void> _detectLanIp() async {
    try {
      final devices = await NetworkInterface.list(type: InternetAddressType.IPv4);
      for (final device in devices) {
        for (final addr in device.addresses) {
          if (addr.isLoopback || addr.address.startsWith('169.254.')) continue;
          if (!mounted) return;
          setState(() => _localAddress = addr.address);
          return;
        }
      }
    } catch (_) {}
  }

  Future<void> _stop() async {
    if (_starting) return;
    setState(() { _starting = true; _alert = ''; });
    try {
      if (_internet) await _cloudflare.stopTunnel();
    } catch (e) {
      _warn('Tunnel shutdown warning: $e');
    } finally {
      _service.invoke('session.stop');
      _tokenInput.clear();
      _domainInput.clear();
      _hadTunnelConnection = false;
      _tunnelConnected = false;
      _tunnelState = 'Not connected';
      if (mounted) setState(() { _state = {'running': false}; _phase = 0; _starting = false; _syncInfinity(); });
    }
  }

  Future<void> _openUrl(String url) async {
    if (!url.startsWith('https://') && !url.startsWith('http://127.0.0.1:') &&
        !url.startsWith('http://localhost:') && !url.startsWith('http://192.168.') &&
        !url.startsWith('http://10.')) {
      _warn('Refusing to open an unexpected link.'); return;
    }
    try {
      if (!await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication)) {
        _warn('No browser available to open the invitation.');
      }
    } catch (e) { _warn('Cannot open browser: $e'); }
  }

  String _inviteUrl(int i) {
    if (i < 0 || i >= _invites.length) return '';
    String link = _invites[i]['url']?.toString() ?? '';
    if (!_internet && _localAddress.isNotEmpty) {
      link = link.replaceFirst('http://127.0.0.1:8787', 'http://$_localAddress:8787');
    }
    return link;
  }

  Future<void> _scan() async {
    final url = await Navigator.of(context).push<String>(MaterialPageRoute(builder: (_) => const ScanInvitePage()));
    if (url != null && mounted) await _openUrl(url);
  }

  Widget _panel({required Widget child}) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22),
      border: Border.all(color: const Color(0xFFDCE9FA))),
    child: child,
  );

  Widget _startPanel() {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const SizedBox(height: 32),
      Center(child: InfinityEmblem(controller: _infinity, height: 114, animate: false)),
      const SizedBox(height: 14),
      const Center(child: Text('FACO CRUMBLE', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800, letterSpacing: 2, color: facoInk))),
      const SizedBox(height: 6),
      const Center(child: Text('Speak. Disconnect. Crumble.', style: TextStyle(fontSize: 14, color: facoSoft))),
      const SizedBox(height: 36),
      _panel(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const Text('Your phone. Your private session.', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: facoInk)),
        const SizedBox(height: 8),
        const Text('Host for up to ten people. Your phone coordinates calls and messages, then destroys temporary access when you end the session.', style: TextStyle(color: facoSoft)),
        const SizedBox(height: 21),
        FilledButton.icon(onPressed: () => setState(() => _phase = 1), icon: const Icon(Icons.cell_tower_rounded),
          label: const Text('Host session'), style: FilledButton.styleFrom(minimumSize: const Size(10, 55))),
        const SizedBox(height: 9),
        OutlinedButton.icon(onPressed: _scan, icon: const Icon(Icons.qr_code_scanner_rounded),
          label: const Text('Join session'), style: OutlinedButton.styleFrom(minimumSize: const Size(10, 55))),
      ])),
    ]);
  }

  Widget _setupPanel() => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    const SizedBox(height: 14),
    TextButton.icon(onPressed: () => setState(() => _phase = 0), icon: const Icon(Icons.arrow_back), label: const Text('Back')),
    const SizedBox(height: 10),
    const Text('Create a private session', style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold, color: facoInk)),
    const SizedBox(height: 9),
    const Text('Invitations are generated on this phone, then become invalid when the session ends.', style: TextStyle(color: facoSoft)),
    const SizedBox(height: 22),
    _panel(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const Text('Who can join?', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: facoInk)),
      const SizedBox(height: 8),
      Text('$_participantCount private invitation${_participantCount == 1 ? '' : 's'}', style: const TextStyle(color: facoSoft)),
      Slider(value: _participantCount.toDouble(), min: 1, max: 10, divisions: 9, label: '$_participantCount',
        onChanged: (v) => setState(() => _participantCount = v.round())),
      const Divider(height: 28),
      SwitchListTile.adaptive(contentPadding: EdgeInsets.zero, value: _internet,
        title: const Text('Internet voice + messages'),
        subtitle: const Text('Use a Cloudflare tunnel connected from this phone.'),
        onChanged: (v) => setState(() => _internet = v)),
      if (_internet) ...[
        const SizedBox(height: 8),
        TextField(controller: _domainInput, keyboardType: TextInputType.url, autocorrect: false,
          decoration: const InputDecoration(labelText: 'Public HTTPS address', hintText: 'https://talk.example.com')),
        const SizedBox(height: 12),
        TextField(controller: _tokenInput, obscureText: true, autocorrect: false, enableSuggestions: false,
          decoration: const InputDecoration(labelText: 'Cloudflare tunnel token', hintText: 'Paste tunnel connector token')),
        const SizedBox(height: 9),
        const Text('Configure a Cloudflare named tunnel once to point at http://127.0.0.1:8787. FACO does not save the token.',
          style: TextStyle(fontSize: 12, color: facoSoft)),
      ] else ...[
        const SizedBox(height: 10),
        const Text('Local Wi-Fi mode provides messaging. Android browser microphone access generally requires HTTPS, so internet mode is recommended for calls.',
          style: TextStyle(color: Color(0xFF9D641D))),
      ],
      const SizedBox(height: 20),
      FilledButton.icon(onPressed: _starting ? null : _host,
        icon: _starting ? const SizedBox(width: 17, height: 17, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.play_arrow_rounded),
        label: Text(_starting ? 'Starting phone server…' : 'Start session'),
        style: FilledButton.styleFrom(minimumSize: const Size(10, 54))),
    ])),
  ]);

  Widget _livePanel() {
    final publicReady = !_internet || _tunnelConnected;
    final url = _selectedQR == 0 ? _state['baseUrl']?.toString() ?? '' : _inviteUrl(_selectedQR - 1);
    final selected = _selectedQR == 0 ? 'Public landing page' : 'Person ${_selectedQR.toString().padLeft(2, '0')}';
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const SizedBox(height: 14),
      Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Session is live', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: facoInk)),
          const SizedBox(height: 3),
          Text('$_online online · $_activeCalls active call${_activeCalls == 1 ? '' : 's'}', style: const TextStyle(color: facoSoft)),
        ])),
        IconButton(tooltip: 'Session diagnostics', onPressed: _showDoctor, icon: const Icon(Icons.monitor_heart_outlined)),
      ]),
      const SizedBox(height: 16),
      _panel(child: Column(children: [
        InfinityEmblem(controller: _infinity, height: 100, animate: _activeCalls > 0 && !_reducedMotion),
        Text(_activeCalls > 0 ? 'Infinity is active · Voice connected' : 'Waiting for conversations',
          style: const TextStyle(color: facoSoft)),
        const SizedBox(height: 14),
        Row(children: [
          Icon(publicReady ? Icons.lock_outline_rounded : Icons.sync_rounded, size: 18,
            color: publicReady ? const Color(0xFF187458) : const Color(0xFFAB7219)),
          const SizedBox(width: 8),
          Expanded(child: Text(_internet ? 'Cloudflare: $_tunnelState' : 'Local Wi-Fi session', style: const TextStyle(color: facoInk))),
        ]),
        const SizedBox(height: 6),
        Row(children: [
          const Icon(Icons.shield_outlined, size: 18, color: facoBlue),
          const SizedBox(width: 8),
          Expanded(child: Text('Credential set ${_state['epoch'] ?? 1} · Rotates on reset', style: const TextStyle(color: facoSoft, fontSize: 12))),
        ]),
      ])),
      const SizedBox(height: 14),
      _panel(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const Text('Share an invitation', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: facoInk)),
        const SizedBox(height: 5),
        const Text('Select a QR. Every participant has a different key.', style: TextStyle(color: facoSoft)),
        const SizedBox(height: 12),
        Wrap(spacing: 7, runSpacing: 7, children: [
          ChoiceChip(label: const Text('Link only'), selected: _selectedQR == 0, onSelected: (_) => setState(() => _selectedQR = 0)),
          ...List.generate(_invites.length, (i) => ChoiceChip(label: Text('${i + 1}'),
            selected: _selectedQR == i + 1, onSelected: (_) => setState(() => _selectedQR = i + 1))),
        ]),
        const SizedBox(height: 15),
        Center(child: Text(selected, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: facoInk))),
        const SizedBox(height: 9),
        if (publicReady && url.isNotEmpty) ...[
          Center(child: QrImageView(data: url, size: 236, padding: const EdgeInsets.all(16),
            backgroundColor: Colors.white, errorCorrectionLevel: QrErrorCorrectLevel.M)),
          SelectableText(url, style: const TextStyle(fontSize: 11, color: facoSoft)),
        ] else const Padding(padding: EdgeInsets.all(25), child: Center(child: Text('Awaiting secure tunnel connection. No invitation shared yet.', textAlign: TextAlign.center, style: TextStyle(color: facoSoft)))),
        const SizedBox(height: 8),
        if (_invites.isNotEmpty) OutlinedButton.icon(
          onPressed: () => _openUrl((_invites[0]['url'] as String).replaceFirst(
                Uri.parse(_invites[0]['url'] as String).origin, 'http://127.0.0.1:8787')),
          icon: const Icon(Icons.call_rounded), label: const Text('Join as Person 01 (on this phone)'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(onPressed: () => _service.invoke('session.rotate'),
          icon: const Icon(Icons.refresh), label: const Text('Rotate all QR invitations')),
      ])),
      const SizedBox(height: 18),
      OutlinedButton.icon(onPressed: _starting ? null : _confirmStop,
        icon: const Icon(Icons.delete_outline), label: const Text('Crumble session · disconnect everyone'),
        style: OutlinedButton.styleFrom(minimumSize: const Size(10, 54), foregroundColor: const Color(0xFFB54640))),
      const SizedBox(height: 12),
    ]);
  }

  Future<void> _confirmStop() async {
    final yes = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('End this entire session?'),
      content: const Text('All calls disconnect, QR credentials expire, and the phone server and Cloudflare connection stop.'),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Keep running')),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Crumble'))],
    ));
    if (yes == true) await _stop();
  }

  void _showDoctor() {
    showModalBottomSheet<void>(context: context, isScrollControlled: true, showDragHandle: true, builder: (ctx) => SafeArea(child: Padding(
      padding: const EdgeInsets.all(22),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('FACO Quick Doctor', style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800)),
        const SizedBox(height: 16),
        Text('Phone server: ${_running ? 'Running' : 'Stopped'}'),
        Text('Connected participants: $_online / $_participantCount'),
        Text('Active voice rooms: $_activeCalls'),
        Text('Tunnel: ${_internet ? _tunnelState : 'Not required (local)'}'),
        Text('QR credential rotation: ${_state['epoch'] ?? 0}'),
        const SizedBox(height: 12),
        SwitchListTile.adaptive(title: const Text('Reduced motion'), value: _reducedMotion,
          onChanged: (v) { setState(() { _reducedMotion = v; _syncInfinity(); }); Navigator.pop(ctx); _showDoctor(); }),
        const SizedBox(height: 12),
        const Text('This app does not store call recordings or server message history. Browsers and Cloudflare may still retain connection metadata.', style: TextStyle(fontSize: 12, color: facoSoft)),
      ]),
    )));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(backgroundColor: facoMist, titleSpacing: 22,
        title: const Text('FACO', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 3, color: facoInk)),
        actions: [if (_phase != 2) IconButton(tooltip: 'Scan invite', onPressed: _scan, icon: const Icon(Icons.qr_code_scanner)), const SizedBox(width: 8)]),
      body: SafeArea(child: LayoutBuilder(builder: (context, constraints) {
        return SingleChildScrollView(padding: const EdgeInsets.symmetric(horizontal: 16), child: Center(child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 580), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            if (_alert.isNotEmpty) Container(margin: const EdgeInsets.only(top: 10, bottom: 6), padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: const Color(0xFFFFEEE9), borderRadius: BorderRadius.circular(12)),
              child: Row(children: [Expanded(child: Text(_alert, style: const TextStyle(color: Color(0xFF944339)))), IconButton(onPressed: () => _warn(''), icon: const Icon(Icons.close), tooltip: 'Dismiss message')])),
            if (_phase == 0) _startPanel() else if (_phase == 1) _setupPanel() else _livePanel(),
            const SizedBox(height: 14),
            const Center(child: Text('FACO · Private by default · v0.6.0', style: TextStyle(fontSize: 12, color: facoSoft))),
            const SizedBox(height: 22),
          ]),
        )));
      })),
    );
  }

  @override
  void dispose() {
    _infinity.dispose();
    _sessionStream?.cancel();
    _errorStream?.cancel();
    _tunnelStream?.cancel();
    _tunnelErrors?.cancel();
    _tokenInput.dispose();
    _domainInput.dispose();
    // Host deliberately stays alive when screen/activity closes. It ends only
    // through "Crumble session", Android foreground service Stop, or OS kill.
    super.dispose();
  }
}

class ScanInvitePage extends StatefulWidget {
  const ScanInvitePage({super.key});
  @override State<ScanInvitePage> createState() => _ScanInvitePageState();
}

class _ScanInvitePageState extends State<ScanInvitePage> {
  bool _done = false;
  String _message = '';
  void _onDetect(BarcodeCapture capture) {
    if (_done || capture.barcodes.isEmpty) return;
    final raw = capture.barcodes.first.rawValue;
    final uri = Uri.tryParse(raw ?? '');
    final role = RegExp(r'^user(0[1-9]|10)$');
    Map<String, String> fragment;
    try { fragment = uri == null ? {} : Uri.splitQueryString(uri.fragment); }
    catch (_) { fragment = {}; }
    if (uri == null || (uri.scheme != 'https' && uri.scheme != 'http') || uri.host.isEmpty ||
        (uri.scheme == 'http' && !uri.host.startsWith('192.168.') && !uri.host.startsWith('10.') && uri.host != '127.0.0.1') ||
        !role.hasMatch(fragment['role'] ?? '') ||
        !RegExp(r'^[A-Za-z0-9_-]{30,128}$').hasMatch(fragment['key'] ?? '')) {
      setState(() => _message = 'This is not a private FACO invitation QR.');
      return;
    }
    _done = true;
    Navigator.of(context).pop(uri.toString());
  }
  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Scan FACO invite')),
    body: SafeArea(child: Column(children: [
      const Padding(padding: EdgeInsets.all(15), child: Text('Scan a Person QR from a live FACO Crumble session. A public-link-only QR does not grant entry.', textAlign: TextAlign.center)),
      Expanded(child: MobileScanner(onDetect: _onDetect)),
      if (_message.isNotEmpty) Padding(padding: const EdgeInsets.all(15), child: Text(_message)),
    ])),
  );
}

class InfinityEmblem extends StatelessWidget {
  const InfinityEmblem({super.key, required this.controller, required this.height, required this.animate});
  final AnimationController controller;
  final double height;
  final bool animate;
  @override Widget build(BuildContext context) => AnimatedBuilder(animation: controller, builder: (_, _) =>
    SizedBox(width: height * 1.9, height: height,
      child: CustomPaint(painter: InfinityPainter(t: animate ? controller.value : -1))));
}

class InfinityPainter extends CustomPainter {
  InfinityPainter({required this.t});
  final double t;
  Offset position(Size s, double a) {
    final w = s.width, h = s.height;
    return Offset(w / 2 + w * 0.405 * math.sin(a), h / 2 + h * 0.38 * math.sin(2 * a) / 1.7);
  }
  @override void paint(Canvas canvas, Size size) {
    final track = Path();
    for (var i = 0; i <= 360; i++) {
      final pos = position(size, i / 360 * math.pi * 2);
      if (i == 0) { track.moveTo(pos.dx, pos.dy); } else { track.lineTo(pos.dx, pos.dy); }
    }
    final shadow = Paint()..color = const Color(0xFF89ADDE).withValues(alpha: .25)..strokeWidth = 15..style = PaintingStyle.stroke..strokeCap = StrokeCap.round;
    canvas.drawPath(track, shadow);
    final outline = Paint()..shader = const LinearGradient(colors: [Color(0xFF7CB7FA), facoBlue, Color(0xFF103F9A)])
      .createShader(Offset.zero & size)..strokeWidth = 9..style = PaintingStyle.stroke..strokeCap = StrokeCap.round;
    canvas.drawPath(track, outline);
    if (t >= 0) {
      final p = position(size, t * math.pi * 2);
      canvas.drawCircle(p, 13, Paint()..color = const Color(0xFF6CE0FF).withValues(alpha: .23));
      canvas.drawCircle(p, 7, Paint()..color = const Color(0xFFE9FDFF));
      canvas.drawCircle(p, 4, Paint()..color = const Color(0xFF12A7ED));
    }
  }
  @override bool shouldRepaint(InfinityPainter old) => old.t != t;
}
