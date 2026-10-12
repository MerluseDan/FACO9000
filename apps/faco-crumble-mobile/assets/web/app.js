/* FACO Crumble v0.5: Cloudlight Electric infinity, session-only options, equal-call WebRTC + chat. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const ui = {
    entryScreen: $('entryScreen'), nameForm: $('nameForm'), nameInput: $('nameInput'),
    rememberName: $('rememberName'), nameNext: $('nameNext'), entryError: $('entryError'),
    appShell: $('appShell'), selfName: $('selfName'), selfAvatar: $('selfAvatar'),
    socketLed: $('socketLed'), socketText: $('socketText'), onlineCount: $('onlineCount'),
    contacts: $('contacts'), selectedTarget: $('selectedTarget'), callPanel: document.querySelector('.call-panel'),
    callStatus: $('callStatus'), callDetail: $('callDetail'), participants: $('participants'),
    incomingActions: $('incomingActions'), regularActions: $('regularActions'),
    callButton: $('callButton'), answerButton: $('answerButton'), declineButton: $('declineButton'),
    endButton: $('endButton'), modeControls: $('modeControls'), pttMode: $('pttMode'),
    handsfreeMode: $('handsfreeMode'), pttButton: $('pttButton'), micHint: $('micHint'),
    errorMessage: $('errorMessage'), soundButton: $('soundButton'),
    chatRecipient: $('chatRecipient'), chatHistory: $('chatHistory'),
    chatForm: $('chatForm'), chatInput: $('chatInput'), chatSend: $('chatSend'),
    leaveButton: $('leaveButton'), audioRack: $('audioRack'),
    callChannelLabel: $('callChannelLabel'), progressLine: $('progressLine'), progressText: $('progressText'),
    viewCallButton: $('viewCallButton'), viewChatButton: $('viewChatButton'),
    unreadPip: $('unreadPip'), callDock: $('callDock'),
    optionsButton: $('optionsButton'), optionsBackdrop: $('optionsBackdrop'),
    optionsPanel: $('optionsPanel'), optionsClose: $('optionsClose'),
    audioInputSelect: $('audioInputSelect'), audioOutputSelect: $('audioOutputSelect'),
    testMicButton: $('testMicButton'), testSpeakerButton: $('testSpeakerButton'),
    motionToggle: $('motionToggle'), focusToggle: $('focusToggle'), alertToggle: $('alertToggle'),
    resetOptionsButton: $('resetOptionsButton'), cancelOptionsButton: $('cancelOptionsButton'),
    saveOptionsButton: $('saveOptionsButton'), doctorButton: $('doctorButton'),
    doctorResult: $('doctorResult'), deviceHint: $('deviceHint'),
    settingsProgress: $('settingsProgress'), settingsProgressText: $('settingsProgressText'),
  };
  const NAME_COOKIE = 'faco_crumble_name';
  const COOKIE_SECONDS = 30 * 24 * 60 * 60;
  const MAX_LOCAL_MESSAGES = 100;
  let identity = null;
  let displayName = '';
  let socket = null;
  let authenticated = false;
  let blocked = false;
  let retries = 0;
  let reconnectTimer = 0;
  let iceServers = [];
  let people = [];
  let selected = null;
  let chatTarget = '';
  let phase = 'offline'; // offline, idle, dialing, ringing, incoming, live
  let activeRoom = null;
  let pending = null;
  let lastInviteTarget = null;
  const roomPeople = new Map();
  const connections = new Map();
  const messages = new Map();
  let microphone = null;
  let mode = 'ptt';
  let transmitting = false;
  const speaking = new Set();
  let soundNeeded = false;
  let alertText = '';
  // Deliberately memory-only. Session preferences never touch cookies, localStorage or sessionStorage.
  const defaults = () => ({inputId:'', outputId:'', motion:true, focus:false, alert:false});
  let options = defaults();
  let currentView = 'call';
  let unreadMessages = 0;
  let optionsOpen = false;
  let optionsBusy = false;
  let lastFocusedElement = null;
  const audioConstraints = deviceId => ({audio: {
    echoCancellation: true, noiseSuppression: true, autoGainControl: true,
    ...(deviceId ? {deviceId: {exact: deviceId}} : {}),
  }, video: false});

  function getQR() {
    const params = new URLSearchParams(location.hash.slice(1));
    const role = params.get('role');
    const token = params.get('key');
    if (location.hash) history.replaceState(null, '', location.pathname); // only visible address, not browser history
    return /^user(?:0[1-9]|10)$/.test(role || '') && /^[A-Za-z0-9_-]{30,128}$/.test(token || '') ? {role, token} : null;
  }
  function validName(value) {
    const name = String(value || '').trim().normalize('NFC');
    return Array.from(name).length >= 1 && Array.from(name).length <= 40 && !/[\p{C}]/u.test(name);
  }
  function cookieValue() {
    try {
      const match = document.cookie.split('; ').find(s => s.startsWith(NAME_COOKIE + '='));
      return match ? decodeURIComponent(match.slice(NAME_COOKIE.length + 1)) : '';
    } catch (_) { return ''; }
  }
  function rememberCookie(name) {
    const secure = location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = `${NAME_COOKIE}=${encodeURIComponent(name)}; Max-Age=${COOKIE_SECONDS}; Path=/; SameSite=Strict${secure}`;
  }
  function clearCookie() {
    document.cookie = `${NAME_COOKIE}=; Max-Age=0; Path=/; SameSite=Strict`;
  }
  function label(role) {
    if (role === identity?.role) return displayName || 'You';
    const info = people.find(p => p.role === role);
    return (info && info.online && info.name) || roomPeople.get(role) ||
      (/^user\d\d$/.test(role || '') ? `Person ${role.slice(-2)}` : 'Person');
  }
  function peer(role) { return people.find(p => p.role === role); }
  function memberOnline(role) { return !!peer(role)?.online; }
  function canInvite() {
    if (!authenticated || !selected || selected === identity?.role) return false;
    const person = peer(selected);
    return !!person?.online && !person.busy && !roomPeople.has(selected) && !['incoming', 'ringing', 'dialing'].includes(phase);
  }
  function announce(text) {
    alertText = text || '';
    ui.errorMessage.textContent = alertText;
    ui.errorMessage.classList.toggle('hidden', !alertText);
  }
  function send(type, extra = {}) {
    if (!socket || socket.readyState !== WebSocket.OPEN || !authenticated) return false;
    socket.send(JSON.stringify({type, ...extra}));
    return true;
  }
  function initialCookie() {
    const saved = cookieValue();
    if (validName(saved)) {
      ui.rememberName.checked = true;
      ui.nameInput.value = saved;
    }
    ui.nameNext.disabled = !validName(ui.nameInput.value);
  }
  function enter(event) {
    event.preventDefault();
    if (!validName(ui.nameInput.value)) {
      ui.entryError.textContent = 'Use 1–40 characters, not spaces alone.';
      ui.entryError.classList.remove('hidden');
      return;
    }
    if (!identity) {
      ui.entryError.textContent = 'Scan your own private QR. The public link does not grant entry.';
      ui.entryError.classList.remove('hidden');
      return;
    }
    displayName = ui.nameInput.value.trim().normalize('NFC');
    if (ui.rememberName.checked) rememberCookie(displayName);
    else if (cookieValue()) clearCookie();
    ui.nameInput.value = '';
    ui.entryError.textContent = '';
    ui.entryError.classList.add('hidden');
    ui.entryScreen.classList.add('hidden');
    ui.appShell.classList.remove('hidden');
    setView('call');
    phase = 'offline';
    render();
    connect();
  }
  function resetCall() {
    for (const role of Array.from(connections.keys())) closePeer(role);
    if (microphone) {
      for (const track of microphone.getTracks()) track.stop();
      microphone = null;
    }
    activeRoom = null;
    pending = null;
    roomPeople.clear();
    transmitting = false;
    speaking.clear();
    lastInviteTarget = null;
    soundNeeded = false;
    ui.soundButton.classList.add('hidden');
    for (const key of Array.from(messages.keys())) if (key.startsWith('room:')) messages.delete(key);
    if (chatTarget === 'room') chatTarget = selected || '';
    phase = authenticated ? 'idle' : 'offline';
    render();
  }
  function leave(showUI = true) {
    optionsBusy = false;
    closeOptions();
    options = defaults();
    applyVisualOptions();
    setView('call');
    unreadMessages = 0;
    blocked = true;
    clearTimeout(reconnectTimer);
    if (activeRoom) send('end', {id: activeRoom});
    else if (pending) send('decline', {id: pending.id});
    if (socket) { const old = socket; socket = null; try {old.close();} catch (_) {} }
    authenticated = false;
    resetCall();
    identity = null;
    displayName = '';
    people = [];
    selected = null;
    chatTarget = '';
    messages.clear();
    iceServers = [];
    alertText = '';
    ui.chatInput.value = '';
    ui.audioInputSelect.replaceChildren(createDeviceOption('', 'System microphone'));
    ui.audioOutputSelect.replaceChildren(createDeviceOption('', 'System output'));
    ui.deviceHint.textContent = 'Use HTTPS and allow microphone access when requested.';
    settingsFields();
    ui.doctorResult.textContent = 'Check your browser, microphone support, network and audio capabilities.';
    ui.chatHistory.replaceChildren();
    ui.chatRecipient.replaceChildren();
    ui.contacts.replaceChildren();
    ui.participants.replaceChildren();
    ui.nameInput.value = '';
    ui.selfName.textContent = 'You';
    ui.selfAvatar.textContent = 'Y';
    ui.selectedTarget.textContent = 'Choose someone';
    ui.onlineCount.textContent = 'Offline';
    ui.callStatus.textContent = 'Private line closed';
    ui.callDetail.textContent = '';
    ui.errorMessage.textContent = '';
    document.title = 'FACO Crumble | Private conversations';
    if (showUI) {
      ui.appShell.classList.add('hidden');
      ui.entryScreen.classList.remove('hidden');
      ui.entryError.textContent = 'Your session has ended. Scan a fresh invitation to come back.';
      ui.entryError.classList.remove('hidden');
      initialCookie();
      ui.nameNext.disabled = true; // invite destroyed; a name alone cannot reconnect
    }
  }
  function renderPeople() {
    ui.contacts.replaceChildren();
    const others = people.filter(p => p.role !== identity?.role);
    for (const item of others) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'person-button' + (!item.online ? ' offline' : '') + (selected === item.role ? ' selected' : '');
      button.dataset.role = item.role;
      button.setAttribute('aria-pressed', String(selected === item.role));
      const avatar = document.createElement('span'); avatar.className = 'avatar';
      avatar.textContent = item.online && item.name ? Array.from(item.name)[0].toUpperCase() : item.role.slice(-2);
      const copy = document.createElement('span'); copy.className = 'person-copy';
      const name = document.createElement('b'); name.textContent = label(item.role);
      const detail = document.createElement('small'); detail.textContent = !item.online ? 'Offline' :
        roomPeople.has(item.role) && activeRoom ? 'In your call' : item.busy ? 'Busy' : 'Online · available';
      copy.append(name, detail);
      const badge = document.createElement('span'); badge.className = 'person-badge'; badge.textContent = item.online ? '●' : '◌';
      button.append(avatar, copy, badge);
      button.addEventListener('click', () => {
        selected = item.role;
        chatTarget = item.role;
        render();
      });
      ui.contacts.append(button);
    }
  }
  function renderChatTargets() {
    const snapshot = people.map(p => `${p.role}:${p.online}:${p.name || ''}`).join('|') + ':' +
      (activeRoom ? 'room' : 'idle') + ':' + (roomPeople.size >= 2);
    if (ui.chatRecipient.dataset.snapshot !== snapshot) {
      ui.chatRecipient.dataset.snapshot = snapshot;
      ui.chatRecipient.replaceChildren();
      const circle = document.createElement('option');
      circle.value = 'circle'; circle.textContent = 'Everyone online';
      ui.chatRecipient.append(circle);
      if (activeRoom && roomPeople.size >= 2) {
        const group = document.createElement('option'); group.value = 'room'; group.textContent = 'Everyone in call';
        ui.chatRecipient.append(group);
      }
      for (const item of people) {
        if (item.role === identity?.role) continue;
        const choice = document.createElement('option');
        choice.value = item.role;
        choice.textContent = `${label(item.role)} ${item.online ? '' : '· offline'}`;
        ui.chatRecipient.append(choice);
      }
    }
    if (chatTarget === 'room' && (!activeRoom || roomPeople.size < 2)) chatTarget = selected || '';
    if (!chatTarget || !Array.from(ui.chatRecipient.options).some(x => x.value === chatTarget)) {
      chatTarget = ui.chatRecipient.options[0]?.value || '';
    }
    ui.chatRecipient.value = chatTarget;
    const canSend = authenticated && (chatTarget === 'circle' ? people.filter(p => p.online).length >= 2 : chatTarget === 'room' ? !!activeRoom && roomPeople.size > 1 : memberOnline(chatTarget));
    ui.chatInput.disabled = !canSend;
    ui.chatSend.disabled = !canSend || !ui.chatInput.value.trim();
  }
  function chatKey(target, from = '') {
    return target === 'circle' ? 'circle' : target === 'room' ? `room:${activeRoom}` : (from === identity?.role ? target : from);
  }
  function showChat() {
    const key = chatTarget === 'circle' ? 'circle' : chatTarget === 'room' ? `room:${activeRoom}` : chatTarget;
    const all = messages.get(key) || [];
    ui.chatHistory.replaceChildren();
    if (!all.length) {
      const empty = document.createElement('p'); empty.className = 'empty-chat';
      empty.textContent = chatTarget === 'circle' ? 'Send a message to everyone currently online. No history is kept on the server.' :
        chatTarget === 'room' ? 'Group messages disappear when the call ends.' :
        'No messages in this session. Type below to send a private note.';
      ui.chatHistory.append(empty);
      return;
    }
    for (const item of all) {
      const bubble = document.createElement('div');
      bubble.className = 'bubble' + (item.from === identity?.role ? ' mine' : '');
      const by = document.createElement('small');
      by.textContent = item.from === identity?.role ? 'You' : item.fromName || label(item.from);
      const text = document.createElement('span'); text.textContent = item.text;
      bubble.append(by, text);
      ui.chatHistory.append(bubble);
    }
    ui.chatHistory.scrollTop = ui.chatHistory.scrollHeight;
  }
  function render() {
    if (authenticated && !selected) {
      const first = people.find(p => p.role !== identity?.role && p.online) || people.find(p => p.role !== identity?.role);
      if (first) { selected = first.role; if (!chatTarget) chatTarget = selected; }
    }
    const online = people.filter(p => p.online).length;
    ui.socketLed.classList.toggle('connected', authenticated);
    ui.socketText.textContent = authenticated ? 'Connected privately' : blocked ? 'Invite expired' : 'Connecting…';
    ui.onlineCount.textContent = `${online} online`;
    ui.selfName.textContent = displayName || 'You';
    ui.selfAvatar.textContent = displayName ? Array.from(displayName)[0].toUpperCase() : 'Y';
    const named = selected ? label(selected) : 'Choose someone';
    ui.selectedTarget.textContent = named;
    const inGroup = !!activeRoom && roomPeople.size >= 2;
    ui.callPanel.classList.toggle('live', phase === 'live');
    ui.callPanel.classList.toggle('ringing', phase === 'ringing' || phase === 'incoming');
    ui.callChannelLabel.textContent = phase === 'live' ? '● ENCRYPTED VOICE ACTIVE' :
      phase === 'incoming' ? '● SOMEONE IS CALLING' : '● READY WHEN YOU ARE';
    const busyPhase = ['offline', 'dialing', 'ringing'].includes(phase);
    ui.progressLine.classList.toggle('hidden', !busyPhase);
    ui.progressText.textContent = phase === 'dialing' ? 'Requesting microphone access…' :
      phase === 'ringing' ? 'Waiting for someone to answer…' : 'Connecting to your private circle…';
    syncMobileView();
    ui.incomingActions.classList.toggle('hidden', phase !== 'incoming');
    ui.regularActions.classList.toggle('hidden', phase === 'incoming');
    ui.modeControls.classList.toggle('hidden', !['ringing', 'live', 'dialing'].includes(phase));
    ui.pttMode.classList.toggle('selected', mode === 'ptt');
    ui.handsfreeMode.classList.toggle('selected', mode === 'handsfree');
    ui.pttMode.setAttribute('aria-pressed', String(mode === 'ptt'));
    ui.handsfreeMode.setAttribute('aria-pressed', String(mode === 'handsfree'));
    ui.pttButton.classList.toggle('hidden', mode !== 'ptt');
    ui.pttButton.classList.toggle('speaking', transmitting);
    ui.pttButton.disabled = phase !== 'live';
    ui.micHint.textContent = mode === 'handsfree' ? 'Microphone open. Everyone in your call can hear you.' :
      transmitting ? 'Transmitting to everyone in this call.' : speaking.size ? `${Array.from(speaking).map(label).join(', ')} speaking` :
        'Microphone muted until you hold the button.';
    ui.callButton.textContent = activeRoom ? 'Add selected to call +' : 'Call selected ↗';
    ui.callButton.disabled = !(authenticated && canInvite() && (activeRoom || phase === 'idle'));
    ui.endButton.classList.toggle('hidden', !activeRoom || phase === 'incoming');
    ui.participants.replaceChildren();
    if (activeRoom) {
      for (const role of Array.from(roomPeople.keys()).sort()) {
        const pill = document.createElement('span'); pill.textContent = role === identity?.role ? `${displayName} (you)` : label(role);
        ui.participants.append(pill);
      }
    }
    ui.participants.classList.toggle('hidden', !activeRoom);
    switch (phase) {
      case 'offline': ui.callStatus.textContent = 'Reconnecting private line'; ui.callDetail.textContent = 'Keep this browser open to receive calls.'; break;
      case 'idle': ui.callStatus.textContent = 'Ready to connect'; ui.callDetail.textContent = selected ? `${named} ${memberOnline(selected) ? 'is online' : 'is offline'}.` : 'Select a person to call or message.'; break;
      case 'dialing': ui.callStatus.textContent = 'Preparing microphone'; ui.callDetail.textContent = 'The first call needs microphone permission.'; break;
      case 'ringing': ui.callStatus.textContent = 'Ringing…'; ui.callDetail.textContent = `Inviting ${label(lastInviteTarget || selected)}.`; break;
      case 'incoming': ui.callStatus.textContent = 'Incoming call'; ui.callDetail.textContent = `${pending?.fromName || label(pending?.from)} is inviting you ${pending?.members?.length > 1 ? 'to a group conversation' : 'to talk'}.`; break;
      case 'live': ui.callStatus.textContent = `Connected with ${Math.max(roomPeople.size - 1, 0)} ${roomPeople.size === 2 ? 'person' : 'people'}`; ui.callDetail.textContent = 'Private voice is active. Invite another available person at any time.'; break;
      default: break;
    }
    renderPeople();
    renderChatTargets();
    showChat();
    ui.errorMessage.textContent = alertText;
    ui.errorMessage.classList.toggle('hidden', !alertText);
  }
  async function getMicrophone() {
    if (microphone && microphone.active) return microphone;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error('Microphone requires an HTTPS connection and permission.');
    microphone = await navigator.mediaDevices.getUserMedia(audioConstraints(options.inputId));
    applyMode();
    return microphone;
  }
  function applyMode() {
    if (mode !== 'ptt') transmitting = false;
    if (microphone) for (const track of microphone.getAudioTracks()) track.enabled = phase === 'live' && (mode === 'handsfree' || transmitting);
    if (activeRoom && mode !== 'ptt') send('ptt', {id: activeRoom, active: false});
    render();
  }
  function transmit(active) {
    if (phase !== 'live' || mode !== 'ptt' || !microphone) active = false;
    if (transmitting === active) return;
    transmitting = active;
    if (microphone) for (const track of microphone.getAudioTracks()) track.enabled = active;
    if (activeRoom) send('ptt', {id: activeRoom, active});
    render();
  }
  function closePeer(role) {
    const entry = connections.get(role);
    if (!entry) return;
    connections.delete(role);
    entry.pc.ontrack = null;
    entry.pc.onicecandidate = null;
    entry.pc.onconnectionstatechange = null;
    try {entry.pc.close();} catch (_) {}
    entry.audio.srcObject = null;
    entry.audio.remove();
    speaking.delete(role);
  }
  function ensurePeer(role) {
    if (!activeRoom || !roomPeople.has(role) || role === identity?.role) return null;
    if (connections.has(role)) return connections.get(role);
    if (!microphone) return null;
    const pc = new RTCPeerConnection({iceServers});
    const audio = document.createElement('audio');
    audio.autoplay = true; audio.playsInline = true; audio.dataset.peer = role;
    ui.audioRack.append(audio);
    if (options.outputId && typeof audio.setSinkId === 'function') {
      audio.setSinkId(options.outputId).catch(() => {
        ui.deviceHint.textContent = 'The selected output is unavailable; your system output will be used.';
      });
    }
    const item = {pc, audio, candidates: [], offered: false};
    connections.set(role, item);
    for (const track of microphone.getAudioTracks()) pc.addTrack(track, microphone);
    pc.onicecandidate = event => {
      if (activeRoom && roomPeople.has(role)) send('signal', {id: activeRoom, target: role,
        data: {type:'candidate', candidate:event.candidate ? event.candidate.toJSON() : null}});
    };
    pc.ontrack = event => {
      audio.srcObject = event.streams[0] || new MediaStream([event.track]);
      audio.play().catch(() => {soundNeeded = true; ui.soundButton.classList.remove('hidden');});
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === 'failed') announce('Audio to ' + label(role) + ' failed. This network may need a TURN relay.');
    };
    return item;
  }
  async function offerPeer(role) {
    const item = ensurePeer(role);
    if (!item || item.offered || identity.role >= role) return;
    item.offered = true;
    const offer = await item.pc.createOffer();
    if (!activeRoom || !connections.has(role)) return;
    await item.pc.setLocalDescription(offer);
    send('signal', {id: activeRoom, target: role, data: {type: 'offer', sdp: item.pc.localDescription.sdp}});
  }
  async function receiveSignal(data) {
    const {from, id, data: signal} = data;
    if (!activeRoom || activeRoom !== id || !roomPeople.has(from) || !signal) return;
    const item = ensurePeer(from);
    if (!item) return;
    if (signal.type === 'offer') {
      if (from >= identity.role) return;
      await item.pc.setRemoteDescription({type: 'offer', sdp: signal.sdp});
      await drainCandidates(item);
      const answer = await item.pc.createAnswer();
      await item.pc.setLocalDescription(answer);
      send('signal', {id: activeRoom, target: from, data: {type: 'answer', sdp: item.pc.localDescription.sdp}});
    } else if (signal.type === 'answer') {
      if (identity.role >= from || item.pc.signalingState !== 'have-local-offer') return;
      await item.pc.setRemoteDescription({type: 'answer', sdp: signal.sdp});
      await drainCandidates(item);
    } else if (signal.type === 'candidate' && signal.candidate) {
      if (!item.pc.remoteDescription) item.candidates.push(signal.candidate);
      else await item.pc.addIceCandidate(signal.candidate);
    }
  }
  async function drainCandidates(item) {
    const pendingIce = item.candidates.splice(0);
    for (const candidate of pendingIce) await item.pc.addIceCandidate(candidate);
  }
  async function dialOrInvite() {
    if (!canInvite() || (!activeRoom && phase !== 'idle')) return;
    announce('');
    const target = selected;
    if (activeRoom) {
      send('invite', {id: activeRoom, target});
      return;
    }
    phase = 'dialing';
    render();
    try {
      await getMicrophone();
      if (!authenticated || phase !== 'dialing') return;
      lastInviteTarget = target;
      if (!send('dial', {target})) resetCall();
      else { phase = 'ringing'; render(); }
    } catch (err) {
      resetCall();
      announce('Could not use your microphone: ' + (err?.message || String(err)));
    }
  }
  async function answerCall() {
    if (phase !== 'incoming' || !pending) return;
    const request = pending;
    ui.answerButton.disabled = true;
    announce('');
    try {
      await getMicrophone();
      if (pending === request && authenticated) send('answer', {id: request.id});
    } catch (err) {
      send('decline', {id: request.id});
      pending = null; phase = 'idle';
      announce('Microphone access was denied: ' + (err?.message || String(err)));
      render();
    } finally {ui.answerButton.disabled = false;}
  }
  function hangUp() {
    if (pending) send('decline', {id: pending.id});
    else if (activeRoom) send('end', {id: activeRoom});
    resetCall();
  }
  function acceptChat(event) {
    event.preventDefault();
    const text = ui.chatInput.value.trim();
    if (!text || text.length > 2000 || !authenticated || !chatTarget) return;
    if (chatTarget === 'room' && (!activeRoom || roomPeople.size < 2)) return;
    if (chatTarget === 'circle' && people.filter(p => p.online).length < 2) return;
    if (!['room', 'circle'].includes(chatTarget) && !memberOnline(chatTarget)) return;
    if (send('chat', {target:chatTarget, text})) {
      ui.chatInput.value = '';
      renderChatTargets();
    }
  }
  function onServer(data) {
    switch (data.type) {
      case 'ready':
        authenticated = true;
        retries = 0;
        iceServers = Array.isArray(data.iceServers) ? data.iceServers : [];
        people = Array.isArray(data.people) ? data.people : [];
        blocked = false;
        phase = 'idle';
        announce('');
        render();
        break;
      case 'auth-error':
        leave(true);
        ui.entryError.textContent = data.message || 'This invite is unavailable.';
        ui.entryError.classList.remove('hidden');
        break;
      case 'session-expired':
        leave(true);
        ui.entryError.textContent = 'Private QRs were refreshed. Request a new code.';
        ui.entryError.classList.remove('hidden');
        break;
      case 'members':
        people = Array.isArray(data.people) ? data.people : [];
        render();
        break;
      case 'invite-sent':
        if (!activeRoom && phase === 'ringing') {
          activeRoom = data.id;
          roomPeople.set(identity.role, displayName);
        }
        if (data.target) lastInviteTarget = data.target;
        render();
        break;
      case 'incoming':
        if (phase !== 'idle' || activeRoom || pending) break;
        pending = {id:data.id, from:data.from, fromName:data.fromName, members:data.members};
        phase = 'incoming';
        document.title = '☎ Incoming call | FACO Crumble';
        if (navigator.vibrate) navigator.vibrate([130, 90, 130]);
        if (options.alert) playAudioCue().catch(() => {});
        setView('call');
        render();
        break;
      case 'invite-cancelled':
        if (pending?.id === data.id) {
          pending = null;
          phase = 'idle';
          announce('Call invitation cancelled or expired.');
          render();
        }
        break;
      case 'invite-result':
        if (data.reason !== 'accepted') announce(`${label(data.target)}: ${data.reason || 'unavailable'}.`);
        render();
        break;
      case 'joined': {
        pending = null;
        activeRoom = data.id;
        roomPeople.clear();
        for (const item of data.members || []) if (typeof item.role === 'string') roomPeople.set(item.role, item.name || label(item.role));
        phase = 'live';
        document.title = 'FACO Crumble | Private conversations';
        applyMode();
        for (const role of roomPeople.keys()) if (role !== identity.role && identity.role < role) {
          offerPeer(role).catch(err => announce('Audio connection issue: ' + (err?.message || String(err))));
        }
        render();
        break;
      }
      case 'member-joined':
        if (data.id !== activeRoom) break;
        roomPeople.set(data.role, data.name || label(data.role));
        phase = 'live';
        applyMode();
        if (identity.role < data.role) offerPeer(data.role).catch(err => announce('Audio connection issue: ' + (err?.message || String(err))));
        render();
        break;
      case 'member-left':
        if (data.id !== activeRoom) break;
        closePeer(data.role);
        roomPeople.delete(data.role);
        speaking.delete(data.role);
        render();
        break;
      case 'ended':
        if (data.id !== activeRoom && data.id !== pending?.id) break;
        resetCall();
        announce('The conversation has ended.');
        break;
      case 'signal':
        receiveSignal(data).catch(err => announce('Audio signaling problem: ' + (err?.message || String(err))));
        break;
      case 'ptt':
        if (data.id === activeRoom) {
          if (data.active) speaking.add(data.from); else speaking.delete(data.from);
          render();
        }
        break;
      case 'chat': {
        if (typeof data.text !== 'string' || data.text.length > 2000) break;
        const key = data.target === 'circle' ? 'circle' : data.target === 'room' ? `room:${data.id}` : chatKey(data.target, data.from);
        const list = messages.get(key) || [];
        list.push({from:data.from, fromName:data.fromName, text:data.text});
        if (list.length > MAX_LOCAL_MESSAGES) list.shift();
        messages.set(key, list);
        if ((chatTarget === 'room' && data.target === 'room') || key === chatTarget) showChat();
        if (data.from !== identity.role) {
          if (currentView !== 'chat') { unreadMessages += 1; syncMobileView(); }
          if (key !== (chatTarget === 'room' ? `room:${activeRoom}` : chatTarget)) {
            announce('New message from ' + (data.fromName || label(data.from)) + '.');
          }
        }
        break;
      }
      case 'error':
        if (phase === 'ringing' && !activeRoom) resetCall();
        announce(data.message || 'Unable to complete request.');
        break;
      default: break;
    }
  }
  function connect() {
    if (!identity || blocked) return;
    if (socket && [WebSocket.OPEN, WebSocket.CONNECTING].includes(socket.readyState)) return;
    const endpoint = (location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + location.host + '/socket';
    const ws = new WebSocket(endpoint);
    socket = ws;
    ws.addEventListener('open', () => ws.send(JSON.stringify({type:'auth', role:identity.role, token:identity.token, name:displayName})));
    ws.addEventListener('message', event => {
      try {onServer(JSON.parse(event.data));} catch (err) {console.warn('Invalid event received', err);}
    });
    ws.addEventListener('close', () => {
      if (socket !== ws) return;
      authenticated = false;
      people = [];
      resetCall();
      if (!blocked && identity) {
        clearTimeout(reconnectTimer);
        const wait = Math.min(15000, 1300 * Math.pow(1.7, retries++));
        reconnectTimer = setTimeout(connect, wait);
      }
    });
    ws.addEventListener('error', () => {});
  }
  function setView(view) {
    currentView = view === 'chat' && !options.focus ? 'chat' : 'call';
    if (currentView === 'chat') unreadMessages = 0;
    syncMobileView();
  }
  function syncMobileView() {
    const chat = currentView === 'chat' && !options.focus;
    document.body?.classList?.toggle('faco-view-chat', chat);
    ui.viewCallButton.classList.toggle('selected', !chat);
    ui.viewChatButton.classList.toggle('selected', chat);
    ui.viewCallButton.setAttribute('aria-selected', String(!chat));
    ui.viewChatButton.setAttribute('aria-selected', String(chat));
    ui.viewChatButton.disabled = !!options.focus;
    ui.unreadPip.classList.toggle('hidden', unreadMessages === 0 || chat);
    ui.callDock.classList.toggle('hidden', !chat || !['live','ringing','dialing'].includes(phase));
  }
  function applyVisualOptions() {
    document.body?.classList?.toggle('faco-no-motion', !options.motion);
    document.body?.classList?.toggle('faco-focus', options.focus);
    if (options.focus && currentView === 'chat') currentView = 'call';
    syncMobileView();
  }
  function settingsFields() {
    ui.motionToggle.checked = options.motion;
    ui.focusToggle.checked = options.focus;
    ui.alertToggle.checked = options.alert;
    ui.audioInputSelect.value = options.inputId;
    ui.audioOutputSelect.value = options.outputId;
  }
  function progressOptions(text) {
    ui.settingsProgressText.textContent = text || '';
    ui.settingsProgress.classList.toggle('hidden', !text);
    ui.saveOptionsButton.disabled = optionsBusy;
  }
  function createDeviceOption(value, name) {
    const e = document.createElement('option');
    e.value = value;
    e.textContent = name;
    return e;
  }
  async function refreshAudioDevices() {
    if (typeof navigator.mediaDevices?.enumerateDevices !== 'function') {
      ui.deviceHint.textContent = 'Device selection is not exposed by this browser. System devices will be used.';
      return;
    }
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs = [createDeviceOption('', 'System microphone')];
      const outputs = [createDeviceOption('', 'System speaker / headphones')];
      let im = 0, om = 0;
      for (const device of devices) {
        if (device.kind === 'audioinput') inputs.push(createDeviceOption(device.deviceId,
          device.label || `Microphone ${++im}`));
        if (device.kind === 'audiooutput') outputs.push(createDeviceOption(device.deviceId,
          device.label || `Speaker ${++om}`));
      }
      // Keep a previously chosen device even if enumeration temporarily hides its label.
      if (options.inputId && !inputs.some(e => e.value === options.inputId))
        inputs.push(createDeviceOption(options.inputId, 'Previously selected microphone'));
      if (options.outputId && !outputs.some(e => e.value === options.outputId))
        outputs.push(createDeviceOption(options.outputId, 'Previously selected speaker'));
      ui.audioInputSelect.replaceChildren(...inputs);
      ui.audioOutputSelect.replaceChildren(...outputs);
      ui.audioInputSelect.value = options.inputId;
      ui.audioOutputSelect.value = options.outputId;
      const outputSupported = typeof document.createElement('audio').setSinkId === 'function';
      ui.audioOutputSelect.disabled = !outputSupported;
      ui.deviceHint.textContent = outputSupported ?
        'Change devices here, then Apply. Microphone changes work during a call.' :
        'This browser uses your system speaker. Output selection is unavailable.';
    } catch (_) { ui.deviceHint.textContent = 'Device list unavailable. System devices will work where permitted.'; }
  }
  function openOptions() {
    if (optionsOpen) return;
    lastFocusedElement = document.activeElement;
    optionsOpen = true;
    ui.optionsBackdrop.classList.remove('hidden');
    ui.optionsPanel.classList.remove('hidden');
    ui.optionsButton.setAttribute('aria-expanded','true');
    settingsFields();
    ui.optionsPanel.focus?.();
    refreshAudioDevices().catch(() => {});
  }
  function closeOptions() {
    if (!optionsOpen || optionsBusy) return;
    optionsOpen = false;
    ui.optionsBackdrop.classList.add('hidden');
    ui.optionsPanel.classList.add('hidden');
    ui.optionsButton.setAttribute('aria-expanded','false');
    progressOptions('');
    lastFocusedElement?.focus?.();
  }
  async function changeMicrophone(newId) {
    if (!microphone || !navigator.mediaDevices?.getUserMedia) return;
    const replacement = await navigator.mediaDevices.getUserMedia(audioConstraints(newId));
    const newTrack = replacement.getAudioTracks()[0];
    const oldStream = microphone;
    const oldTrack = oldStream.getAudioTracks()[0];
    const switched = [];
    try {
      for (const item of connections.values()) {
        const sender = item.pc.getSenders?.().find(s => s.track?.kind === 'audio');
        if (!sender || typeof sender.replaceTrack !== 'function')
          throw new Error('This browser cannot change microphones while connected.');
        await sender.replaceTrack(newTrack);
        switched.push(sender);
      }
    } catch (err) {
      for (const sender of switched) { try {await sender.replaceTrack(oldTrack);} catch (_) {} }
      for (const track of replacement.getTracks()) track.stop();
      throw err;
    }
    microphone = replacement;
    applyMode();
    for (const track of oldStream.getTracks()) track.stop();
  }
  async function changeOutput(newId) {
    const sounds = Array.from(ui.audioRack.querySelectorAll?.('audio') || []);
    if (!sounds.length) return;
    for (const a of sounds) {
      if (typeof a.setSinkId !== 'function') {
        if (newId) throw new Error('Output device selection is unsupported in this browser.');
        continue;
      }
      await a.setSinkId(newId);
    }
  }
  async function applyOptions() {
    if (optionsBusy) return;
    const next = {
      inputId: ui.audioInputSelect.value || '', outputId: ui.audioOutputSelect.value || '',
      motion: ui.motionToggle.checked, focus: ui.focusToggle.checked, alert: ui.alertToggle.checked,
    };
    optionsBusy = true;
    progressOptions('Applying your session settings…');
    try {
      if (next.inputId !== options.inputId) await changeMicrophone(next.inputId);
      if (next.outputId !== options.outputId) await changeOutput(next.outputId);
      options = next;
      applyVisualOptions();
      ui.deviceHint.textContent = 'Settings applied for this session only. Nothing was stored on this phone.';
    } catch(err) {
      ui.deviceHint.textContent = 'Could not change device: ' + (err?.message || String(err));
      optionsBusy = false;
      progressOptions('');
      return;
    }
    optionsBusy = false;
    progressOptions('');
    closeOptions();
  }
  async function testMicrophone() {
    if (optionsBusy) return;
    if (microphone?.active) { ui.deviceHint.textContent = 'Microphone ready for your live call.'; return; }
    if (!navigator.mediaDevices?.getUserMedia) {
      ui.deviceHint.textContent = 'Microphone test requires HTTPS, a supported browser and permission.'; return;
    }
    optionsBusy = true;
    progressOptions('Checking microphone access…');
    let sample;
    try {
      sample = await navigator.mediaDevices.getUserMedia(audioConstraints(ui.audioInputSelect.value));
      const result = sample.getAudioTracks().length ?
        'Microphone access passed. Test finished; the microphone was released.' : 'No audio track was returned.';
      for (const track of sample.getTracks()) track.stop();
      sample = null;
      await refreshAudioDevices();
      ui.deviceHint.textContent = result;
    } catch (err) { ui.deviceHint.textContent = 'Microphone test failed: ' + (err?.message || String(err)); }
    finally {
      if (sample) for (const track of sample.getTracks()) track.stop();
      optionsBusy = false;progressOptions('');
    }
  }
  async function playAudioCue(deviceId = options.outputId) {
    // One 300ms low-volume WAV; no remote downloads, microphone access, cookies or recordings.
    const rate = 16000, count = 4800;
    const wav = new ArrayBuffer(44 + 2 * count), view = new DataView(wav);
    const word = (offset, value) => view.setUint16(offset,value,true);
    const dword = (offset, value) => view.setUint32(offset,value,true);
    ['R','I','F','F'].forEach((c,i) => view.setUint8(i,c.charCodeAt(0)));
    dword(4, wav.byteLength - 8);
    ['W','A','V','E','f','m','t',' '].forEach((c,i)=>view.setUint8(8+i,c.charCodeAt(0)));
    dword(16,16);word(20,1);word(22,1);dword(24,rate);dword(28,rate*2);word(32,2);word(34,16);
    ['d','a','t','a'].forEach((c,i)=>view.setUint8(36+i,c.charCodeAt(0)));
    dword(40,2*count);
    for (let i=0;i<count;i++) {
      const envelope = Math.min(1,i/400,(count-i)/600);
      view.setInt16(44+2*i, Math.round(Math.sin(2*Math.PI*610*i/rate)*4000*Math.max(0,envelope)),true);
    }
    const url = URL.createObjectURL(new Blob([wav],{type:'audio/wav'}));
    const audio = document.createElement('audio');
    try {
      if (deviceId && typeof audio.setSinkId === 'function') await audio.setSinkId(deviceId);
      audio.src = url;
      await audio.play();
      setTimeout(() => {audio.pause?.();audio.remove?.();URL.revokeObjectURL(url);},650);
    } catch (err) {URL.revokeObjectURL(url);throw err;}
  }
  async function runDoctor() {
    if (optionsBusy) return;
    optionsBusy = true;progressOptions('Running FACO quick diagnostics…');
    const checks = [
      `Secure context: ${location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1' ? 'Passed' : 'Needs HTTPS'}`,
      `WebRTC: ${typeof RTCPeerConnection === 'function' ? 'Available' : 'Unavailable'}`,
      `Microphone API: ${navigator.mediaDevices?.getUserMedia ? 'Available' : 'Unavailable'}`,
      `Signaling: ${authenticated && socket?.readyState === WebSocket.OPEN ? 'Connected' : 'Disconnected'}`,
      `Audio peers: ${connections.size}`,
      `TURN servers: ${iceServers.filter(x => String(x.urls || '').includes('turn:')).length ? 'Configured' : 'Not configured'}`,
      `Session storage: ${'Not used for call preferences or invites'}`,
    ];
    ui.doctorResult.textContent = checks.join('\n');
    optionsBusy = false;progressOptions('');
  }
  ui.viewCallButton.addEventListener('click', () => setView('call'));
  ui.viewChatButton.addEventListener('click', () => setView('chat'));
  ui.callDock.addEventListener('click', () => setView('call'));
  ui.optionsButton.addEventListener('click', openOptions);
  ui.optionsClose.addEventListener('click', closeOptions);
  ui.optionsBackdrop.addEventListener('click', closeOptions);
  ui.cancelOptionsButton.addEventListener('click', closeOptions);
  ui.saveOptionsButton.addEventListener('click', () => applyOptions().catch(err=>{
    ui.deviceHint.textContent = String(err);optionsBusy=false;progressOptions('');
  }));
  ui.resetOptionsButton.addEventListener('click', () => {
    const d=defaults();ui.audioInputSelect.value=d.inputId;ui.audioOutputSelect.value=d.outputId;
    ui.motionToggle.checked=d.motion;ui.focusToggle.checked=d.focus;ui.alertToggle.checked=d.alert;
    ui.deviceHint.textContent='Defaults selected. Tap Apply to use them.';
  });
  ui.testMicButton.addEventListener('click', () => testMicrophone().catch(()=>{}));
  ui.testSpeakerButton.addEventListener('click', () => playAudioCue(ui.audioOutputSelect.value).then(() => {
    ui.deviceHint.textContent = 'Test tone played. If you could not hear it, check your system volume.';
  }).catch(err => {ui.deviceHint.textContent = 'Speaker test failed: '+ (err?.message || String(err));}));
  ui.doctorButton.addEventListener('click', () => runDoctor().catch(()=>{}));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && optionsOpen) closeOptions();
    // Keep keyboard focus inside the options dialog.
    if (event.key === 'Tab' && optionsOpen && document.querySelectorAll) {
      const nodes = Array.from(ui.optionsPanel.querySelectorAll?.('button:not(:disabled),select:not(:disabled),input:not(:disabled)') || []);
      if (!nodes.length) return;
      if (event.shiftKey && document.activeElement === nodes[0]) {event.preventDefault(); nodes[nodes.length-1].focus();}
      else if (!event.shiftKey && document.activeElement === nodes[nodes.length-1]) {event.preventDefault();nodes[0].focus();}
    }
  });
  ui.nameInput.addEventListener('input', () => {
    ui.nameNext.disabled = !validName(ui.nameInput.value);
    ui.entryError.classList.add('hidden');
  });
  ui.rememberName.addEventListener('change', () => {
    // If a previously saved name exists, the visitor can remove it immediately.
    if (!ui.rememberName.checked && cookieValue()) clearCookie();
  });
  ui.nameForm.addEventListener('submit', enter);
  ui.leaveButton.addEventListener('click', () => leave(true));
  ui.callButton.addEventListener('click', dialOrInvite);
  ui.answerButton.addEventListener('click', answerCall);
  ui.declineButton.addEventListener('click', hangUp);
  ui.endButton.addEventListener('click', hangUp);
  ui.pttMode.addEventListener('click', () => {mode = 'ptt'; applyMode();});
  ui.handsfreeMode.addEventListener('click', () => {mode = 'handsfree'; applyMode();});
  ui.chatRecipient.addEventListener('change', event => {chatTarget = event.target.value; render();});
  ui.chatForm.addEventListener('submit', acceptChat);
  ui.chatInput.addEventListener('input', () => {ui.chatSend.disabled = !ui.chatInput.value.trim() || ui.chatInput.disabled;});
  ui.soundButton.addEventListener('click', () => {
    Promise.all(Array.from(ui.audioRack.querySelectorAll('audio')).map(audio => audio.play().catch(() => false)))
      .then(() => {soundNeeded = false; ui.soundButton.classList.add('hidden');});
  });
  ui.pttButton.addEventListener('pointerdown', event => {
    if (event.button !== 0 || phase !== 'live' || mode !== 'ptt') return;
    event.preventDefault();
    try {ui.pttButton.setPointerCapture(event.pointerId);} catch (_) {}
    transmit(true);
  });
  for (const eventName of ['pointerup','pointercancel','pointerleave','lostpointercapture']) {
    ui.pttButton.addEventListener(eventName, () => transmit(false));
  }
  ui.pttButton.addEventListener('keydown', event => {
    if (event.code === 'Space' && !event.repeat) {event.preventDefault(); transmit(true);}
  });
  ui.pttButton.addEventListener('keyup', event => {
    if (event.code === 'Space') {event.preventDefault(); transmit(false);}
  });
  window.addEventListener('blur', () => transmit(false));
  document.addEventListener('visibilitychange', () => {if (document.hidden) transmit(false);});
  window.addEventListener('pagehide', () => leave(false));
  window.addEventListener('pageshow', event => {if (event.persisted) leave(true);});
  // Old FACO versions may have stored a legacy invite in sessionStorage. Clear once.
  try {sessionStorage.removeItem('faco-invite'); sessionStorage.removeItem('faco-talk-mode');} catch (_) {}
  identity = getQR();
  initialCookie();
  render();
})();
