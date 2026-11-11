#!/usr/bin/env python3
"""Apply FACO Android permissions and service metadata to flutter create output.

Idempotent, fails if flutter has not created its Android manifest.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

manifest = Path('android/app/src/main/AndroidManifest.xml')
if not manifest.exists():
    raise SystemExit('ERROR: generate platform with flutter create --platforms=android first')
ANDROID='http://schemas.android.com/apk/res/android'
TOOLS='http://schemas.android.com/tools'
ET.register_namespace('android', ANDROID)
ET.register_namespace('tools', TOOLS)
def a(key):return f'{{{ANDROID}}}{key}'
def t(key):return f'{{{TOOLS}}}{key}'
root = ET.parse(manifest).getroot()
permissions = [
    'android.permission.INTERNET',
    'android.permission.CAMERA',
    'android.permission.RECORD_AUDIO',
    'android.permission.POST_NOTIFICATIONS',
    'android.permission.FOREGROUND_SERVICE',
    'android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE',
    'android.permission.FOREGROUND_SERVICE_DATA_SYNC',
    'android.permission.CHANGE_NETWORK_STATE',
    'android.permission.WAKE_LOCK',
]
existing={e.get(a('name')) for e in root.findall('uses-permission')}
for name in permissions:
    if name not in existing:
        e=ET.Element('uses-permission');e.set(a('name'),name)
        root.insert(0,e)
app=root.find('application')
if app is None:raise SystemExit('ERROR: android manifest has no application')
app.set(a('label'),'FACO Crumble')
app.set(a('usesCleartextTraffic'),'true')   # LAN mode; token required for access
app.set(a('allowBackup'),'false')
service_name='id.flutter.flutter_background_service.BackgroundService'
svc=next((e for e in app.findall('service') if e.get(a('name'))==service_name),None)
if svc is None:
    svc=ET.SubElement(app,'service');svc.set(a('name'),service_name)
svc.set(a('exported'),'false')
svc.set(a('foregroundServiceType'),'connectedDevice')
svc.set(t('replace'),'android:foregroundServiceType,android:exported')
ET.indent(root)
ET.ElementTree(root).write(manifest,encoding='utf-8',xml_declaration=True)
print('FACO Android manifest patched:', manifest)
