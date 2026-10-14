import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:async/async.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:faco_crumble_mobile/crumble_server.dart';

Future<Uint8List> bytes(String name) async => Uint8List.fromList(
    utf8.encode('<!doctype html><title>FACO $name</title>'));

class Peer {
  Peer(this.ws) : queue = StreamQueue<dynamic>(ws.map((e) => jsonDecode(e as String)));
  final WebSocket ws;
  final StreamQueue<dynamic> queue;
  Future<Map<String, dynamic>> next(String type) async {
    for (var i = 0; i < 35; i++) {
      final data = (await queue.next.timeout(const Duration(seconds: 4))) as Map<String, dynamic>;
      if (data['type'] == type) return data;
    }
    throw StateError('Never received $type');
  }
  void send(String type, Map<String, dynamic> data) => ws.add(jsonEncode({'type': type, ...data}));
  Future<void> close() async { await ws.close(); await queue.cancel(); }
}

Future<Peer> connect(CrumbleServer server, String role, String token, String name) async {
  final ws = await WebSocket.connect('ws://127.0.0.1:${server.actualPort}/socket',
      headers: {'Origin': 'http://127.0.0.1:${server.actualPort}'});
  final p = Peer(ws);
  p.send('auth', {'role': role, 'token': token, 'name': name});
  return p;
}

void main() {
  test('Credentials unique and rotate, public URL validates HTTPS', () async {
    final server = CrumbleServer(assetLoader: bytes, port: 0);
    await server.start(participantCount: 10);
    addTearDown(server.stop);
    final values = server.invitationTokens.values.toList();
    expect(values.length, 10);
    expect(values.toSet().length, 10);
    expect(values.every((x) => x.length >= 40), isTrue);
    final previous = server.invitationTokens['user02'];
    server.setPublicUrl('https://voice.example.org');
    expect(server.invitation(1), startsWith('https://voice.example.org/#role=user02&key='));
    server.rotate();
    expect(server.invitationTokens['user02'], isNot(previous));
    expect(() => server.setPublicUrl('http://untrusted.example.org'), throwsArgumentError);
  });

  test('Credential rejection, one-character name, duplicate-device lock', () async {
    final server = CrumbleServer(assetLoader: bytes, port: 0);
    await server.start(participantCount: 2);
    addTearDown(server.stop);
    final bad = await connect(server, 'user01', 'bad', 'A');
    expect((await bad.next('auth-error'))['message'], contains('expired'));
    await bad.close();
    final good = await connect(server, 'user01', server.invitationTokens['user01']!, 'A');
    expect((await good.next('ready'))['name'], 'A');
    final duplicate = await connect(server, 'user01', server.invitationTokens['user01']!, 'Another');
    expect((await duplicate.next('auth-error'))['message'], contains('used'));
    await duplicate.close();
    await good.close();
  });

  test('Calling, joining group, private/circle/room chat, isolation', () async {
    final server = CrumbleServer(assetLoader: bytes, port: 0);
    await server.start(participantCount: 4);
    addTearDown(server.stop);
    final peers = <Peer>[];
    for (var n = 1; n <= 4; n++) {
      final role = 'user${n.toString().padLeft(2, '0')}';
      final peer = await connect(server, role, server.invitationTokens[role]!, 'Person $n');
      expect((await peer.next('ready'))['role'], role);
      peers.add(peer);
    }
    final a = peers[0], b = peers[1], c = peers[2], outsider = peers[3];
    a.send('dial', {'target': 'user02'});
    final incoming = await b.next('incoming');
    expect(incoming['from'], 'user01');
    final id = incoming['id'] as String;
    b.send('answer', {'id': id});
    final joined = await b.next('joined');
    expect((joined['members'] as List).length, 2);
    a.send('invite', {'id': id, 'target': 'user03'});
    final groupInvite = await c.next('incoming');
    expect((groupInvite['members'] as List).length, 2);
    c.send('answer', {'id': id});
    expect((await c.next('joined'))['members'], hasLength(3));
    a.send('signal', {'id': id, 'target': 'user02', 'data': {'type': 'offer', 'sdp': 'sample-sdp'}});
    expect((await b.next('signal'))['from'], 'user01');
    a.send('chat', {'target': 'user02', 'text': 'direct'});
    expect((await b.next('chat'))['text'], 'direct');
    b.send('chat', {'target': 'room', 'text': 'room only'});
    expect((await c.next('chat'))['text'], 'room only');
    a.send('chat', {'target': 'circle', 'text': 'everyone'});
    expect((await outsider.next('chat'))['text'], 'everyone');
    outsider.send('signal', {'id': id, 'target': 'user02', 'data': {'type': 'offer', 'sdp': 'attack'}});
    expect(server.activeCallCount, 1);
    server.rotate();
    expect(server.onlineCount, 0);
    expect(server.activeCallCount, 0);
    for (final peer in peers) { await peer.close(); }
  });


  test('Video status is per-room, late-join aware, and cleared after leaving', () async {
    final server = CrumbleServer(assetLoader: bytes, port: 0);
    await server.start(participantCount: 4);
    addTearDown(server.stop);
    final connections = <Peer>[];
    for (var i = 1; i <= 4; i++) {
      final role = 'user${i.toString().padLeft(2, '0')}';
      final user = await connect(server, role, server.invitationTokens[role]!, 'P$i');
      await user.next('ready');
      connections.add(user);
    }
    addTearDown(() async { for (final p in connections) { await p.close(); } });
    final alice = connections[0], bob = connections[1], chloe = connections[2], outsider = connections[3];
    alice.send('dial', {'target':'user02'});
    final invite = await bob.next('incoming');
    final id = invite['id'] as String;
    bob.send('answer', {'id':id});
    final joined = await bob.next('joined');
    expect((joined['members'] as List).every((x) => x['video'] == false), true);

    alice.send('video', {'id':id, 'enabled':true});
    final enabled = await bob.next('video');
    expect(enabled, containsPair('from','user01'));
    expect(enabled, containsPair('enabled',true));
    outsider.send('video', {'id':id, 'enabled':true}); // no membership => ignored
    bob.send('invite', {'id':id, 'target':'user03'});
    await chloe.next('incoming');
    chloe.send('answer', {'id':id});
    final lateJoin = await chloe.next('joined');
    final lateMembers = (lateJoin['members'] as List).cast<Map>();
    expect(lateMembers.firstWhere((x) => x['role']=='user01')['video'], true);
    expect(lateMembers.firstWhere((x) => x['role']=='user02')['video'], false);

    alice.send('video', {'id':id, 'enabled':false});
    final disabled = await chloe.next('video');
    expect(disabled, containsPair('from','user01'));
    expect(disabled, containsPair('enabled',false));
    bob.send('video', {'id':id, 'enabled':true});
    final bobOn = await chloe.next('video');
    expect(bobOn, containsPair('from','user02'));
    expect(bobOn, containsPair('enabled',true));

    // End this room, then reconnect: video must NOT leak into the next call.
    bob.send('end', {'id':id});
    await bob.next('ended');
    alice.send('end', {'id':id});
    await alice.next('ended');
    // Chloe's room is automatically ended when only one remains.
    await chloe.next('ended');
    bob.send('dial', {'target':'user01'});
    final nextInvite = await alice.next('incoming');
    alice.send('answer', {'id': nextInvite['id']});
    final nextRoom = await alice.next('joined');
    expect((nextRoom['members'] as List).every((x) => x['video'] == false), true);
  });

  test('HTTP static assets and privacy headers, no admin route', () async {
    final server = CrumbleServer(assetLoader: bytes, port: 0);
    await server.start(participantCount: 1);
    addTearDown(server.stop);
    final client = HttpClient();
    addTearDown(client.close);
    var req = await client.getUrl(Uri.parse('http://127.0.0.1:${server.actualPort}/'));
    var res = await req.close();
    expect(res.statusCode, 200);
    expect(res.headers.value('Cache-Control'), contains('no-store'));
    expect(res.headers.value('Permissions-Policy'), contains('camera=(self)'));
    expect(await utf8.decoder.bind(res).join(), contains('FACO'));
    req = await client.getUrl(Uri.parse('http://127.0.0.1:${server.actualPort}/api/state'));
    res = await req.close();
    expect(res.statusCode, 404);
  });
}
