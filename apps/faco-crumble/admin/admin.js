/* FACO Ubuntu QR console. Credentials sent ONLY from 127.0.0.1:admin-port.
   Each QR image includes the full bearer invite and is intentionally sensitive. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const buttons = Array.from(document.querySelectorAll('.slot[data-role]'));
  let adminToken = new URLSearchParams(location.hash.slice(1)).get('admin');
  if (adminToken && /^[A-Za-z0-9_-]{30,128}$/.test(adminToken)) {
    sessionStorage.setItem('faco-admin-key', adminToken);
    history.replaceState(null, '', location.pathname);
  } else adminToken = sessionStorage.getItem('faco-admin-key');
  let selected = 'landing', state = null, imageObjectUrl = null, imageBytes = null;
  let signature = '', participantListSignature = '', busy = false, noticeTimer = 0, errorShown = false, doctorVisible = false;
  const choices = $('guestSlots');

  function tell(message) {
    $('toast').textContent = message;
    $('toast').classList.add('visible');
    clearTimeout(noticeTimer);
    noticeTimer = setTimeout(() => $('toast').classList.remove('visible'), 3200);
  }
  function invite(role) { return state?.invites.find(item => item.role === role); }
  function urlFor(role) { return role === 'landing' ? (state?.baseUrl ? state.baseUrl + '/' : '') : (invite(role)?.url || ''); }
  function titleFor(role) { return role === 'landing' ? 'Cloudflare public link' : `Person ${role.slice(-2)}`; }
  async function api(path, method='GET', data=null) {
    if (!adminToken) throw new Error('Missing local admin key. Open the control link printed in your terminal.');
    const response = await fetch(path, {
      method, cache: 'no-store', credentials: 'omit',
      headers: {'X-FACO-Admin': adminToken, ...(data ? {'Content-Type': 'application/json'} : {})},
      ...(data ? {body: JSON.stringify(data)} : {}),
    });
    if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
    return response;
  }
  async function imageFor(role, expectedSignature) {
    if (imageObjectUrl) URL.revokeObjectURL(imageObjectUrl);
    imageObjectUrl = null; imageBytes = null;
    $('qrImage').classList.add('hidden');
    $('qrImage').removeAttribute('src');
    $('qrLoading').classList.remove('hidden');
    const label = role;
    try {
      const response = await api(`/qr/${encodeURIComponent(role)}.svg`);
      const svg = await response.blob();
      if (selected !== label || !state?.baseUrl || signature !== expectedSignature) return;
      imageBytes = svg;
      imageObjectUrl = URL.createObjectURL(svg);
      $('qrImage').src = imageObjectUrl;
      $('qrImage').classList.remove('hidden');
      $('qrLoading').classList.add('hidden');
    } catch (err) {
      $('qrLoading').textContent = 'QR unavailable: ' + err.message;
      $('qrImage').classList.add('hidden');
    }
  }
  function choose(role) { selected = role; render(true); }
  function navSlot(role, label, online) {
    const item = document.createElement('button');
    item.type = 'button'; item.className = 'slot'; item.dataset.role = role;
    const symbol = document.createElement('span'); symbol.className='slot-symbol'; symbol.textContent=role.slice(-2);
    const words=document.createElement('span'); words.className='slot-copy';
    const title=document.createElement('b'); title.textContent=label;
    const subtitle=document.createElement('small'); subtitle.textContent=online ? 'Online · Ready' : 'Personal QR invitation';
    words.append(title,subtitle);
    const arrow=document.createElement('span'); arrow.className='slot-chevron'; arrow.textContent='›';
    item.append(symbol,words,arrow);
    item.setAttribute('aria-current', String(selected===role));
    item.addEventListener('click',() => choose(role));
    return item;
  }
  function renderDoctor() {
    if (!state || !doctorVisible) return;
    const lines = [
      `Control panel: Passed (localhost-only administrator)`,
      `Public tunnel: ${state.tunnelState === 'Active' ? 'Active' : state.tunnelState}`,
      `HTTPS public address: ${state.baseUrl?.startsWith('https://') ? 'Ready' : 'Not connected'}`,
      `Invitations: ${state.guestCount} separate credentials`,
      `Online people: ${(state.online || []).length}`,
      `Credential edition: ${String(state.epoch).padStart(2,'0')}`,
      'Messages/recordings: Not retained by the app',
      'Android audio & mobile carrier routes: Must be verified on real devices',
    ];
    $('doctorResults').textContent = lines.join('\n');
  }
  function render(forceQR=false) {
    if (!state) return;
    const count = state.guestCount;
    const online = state.online || [];
    if (selected.startsWith('user') && !invite(selected)) selected='landing';
    $('onlineCount').textContent = `${online.length} participant(s) online`;
    $('connectionStatus').classList.toggle('active', state.tunnelState === 'Active');
    $('connectionStatus').lastElementChild.textContent = state.tunnelState === 'Active' ? 'Public link active' : state.tunnelState;
    $('publicUrl').textContent = state.baseUrl || 'Waiting for Cloudflare…';
    $('epochNotice').textContent = `Invitation edition ${String(state.epoch).padStart(2,'0')} · Automatic key refresh enabled`;
    $('guestCount').textContent = String(count);
    $('removeGuest').disabled = count <= 1 || busy;
    $('addGuest').disabled = count >= 10 || busy;
    $('rotateButton').disabled = busy;
    $('edition').textContent = `Edition ${String(state.epoch).padStart(2,'0')}`;
    $('lastRotated').textContent = `${state.reason}. QR credentials are temporary and are not written to disk.`;
    renderDoctor();
    for (const button of buttons) button.setAttribute('aria-current', String(button.dataset.role === selected));
    const listSignature = `${selected}|${state.invites.map(item => item.role).join(',')}|${online.join(',')}`;
    if (listSignature !== participantListSignature) {
      participantListSignature = listSignature;
      const nodes = state.invites.filter(item => item.role.startsWith('user')).map(item =>
        navSlot(item.role, item.label, online.includes(item.role)));
      choices.replaceChildren(...nodes);
    }
    $('selectionTitle').textContent=titleFor(selected);
    $('selectionBadge').textContent = selected === 'landing' ? '00' : selected.slice(-2);
    $('selectionType').textContent = selected === 'landing' ? 'PUBLIC LANDING QR' : 'PRIVATE PARTICIPANT QR';
    $('selectionDescription').textContent = selected === 'landing' ?
      'Opens the website without granting access. Share a personal QR to join.' :
      `Share this private QR. The recipient enters a name, chooses cookie preference and joins as ${titleFor(selected)}. Everyone has equal calling and messaging permissions.`;
    $('qrCaption').textContent = selected === 'landing' ? 'Public entrance · No credentials attached' :
      'Private entry · Secret key embedded in QR';
    const url = urlFor(selected);
    $('inviteUrl').value = url || 'Waiting for Cloudflare…';
    for (const id of ['copyButton','shareButton','saveButton']) $(id).disabled = !url;
    const version = `${state.epoch}:${state.baseUrl}:${selected}`;
    if (version !== signature || forceQR) {
      signature = version;
      $('qrLoading').textContent = url ? 'Preparing QR…' : 'Waiting for a public HTTPS link. This updates automatically.';
      if (url) imageFor(selected, version);
      else {
        if (imageObjectUrl) URL.revokeObjectURL(imageObjectUrl);
        imageObjectUrl = null; imageBytes = null;
        $('qrImage').classList.add('hidden');
        $('qrImage').removeAttribute('src');
        $('qrLoading').classList.remove('hidden');
      }
    }
  }
  async function refresh() {
    try {
      const response = await api('/api/state');
      state = await response.json();
      render(); errorShown = false;
    } catch(err) {
      $('connectionStatus').classList.remove('active');
      $('connectionStatus').lastElementChild.textContent='Control panel disconnected';
      if (!errorShown) { tell(err.message); errorShown=true; }
    }
  }
  async function change(action, data) {
    if (busy) return;
    busy=true; render();
    try {
      const response=await api(`/api/${action}`,'POST', data);
      state=await response.json();
      tell('Codes refreshed. Previously shared QR credentials have expired.');
      render();
    } catch(err) {tell('Could not update: '+err.message);}
    finally {busy=false;render();}
  }
  async function copyLink() {
    const u=urlFor(selected); if (!u) return;
    try {await navigator.clipboard.writeText(u);tell('Link copied to clipboard.');}
    catch(_) { $('inviteUrl').focus(); $('inviteUrl').select(); tell('Select and copy the link above.'); }
  }
  async function shareLink() {
    const u=urlFor(selected); if (!u) return;
    if (navigator.share) {
      try {await navigator.share({title: `FACO ${titleFor(selected)} invite`, text: 'Open this private voice link:', url:u});return;}
      catch (err) { if (err.name==='AbortError') return; }
    }
    await copyLink();
  }
  async function saveQR() {
    if (!imageBytes) return tell('QR is still loading.');
    const link=document.createElement('a');
    link.href=URL.createObjectURL(imageBytes);
    link.download = `FACO_${selected}_invite_${state.epoch}.svg`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 2000);
    tell('QR image saved as SVG. Keep private participant codes secure.');
  }
  $('doctorToggle').addEventListener('click', () => {
    doctorVisible = !doctorVisible;
    $('doctorResults').classList.toggle('hidden', !doctorVisible);
    $('doctorToggle').textContent = doctorVisible ? 'Hide checks ↗' : 'Show checks ↗';
    $('doctorToggle').setAttribute('aria-expanded', String(doctorVisible));
    renderDoctor();
  });
  buttons.forEach(b=>b.addEventListener('click',()=>choose(b.dataset.role)));
  $('copyButton').addEventListener('click',copyLink);
  $('shareButton').addEventListener('click',shareLink);
  $('saveButton').addEventListener('click',saveQR);
  $('removeGuest').addEventListener('click',()=>{if(state.guestCount>1 && !busy)change('guest-count',{count:state.guestCount-1});});
  $('addGuest').addEventListener('click',()=>{if(state.guestCount<10 && !busy)change('guest-count',{count:state.guestCount+1});});
  $('rotateButton').addEventListener('click',()=>{if(!busy)change('rotate',{});});
  if (!adminToken) {
    $('qrLoading').textContent = 'Open the private admin URL printed in the terminal on this Ubuntu computer.';
    tell('Admin key is missing. Use the URL from your server terminal.');
  } else { refresh(); setInterval(refresh, 2500); }
  window.addEventListener('pagehide',()=>{if(imageObjectUrl)URL.revokeObjectURL(imageObjectUrl);});
})();
