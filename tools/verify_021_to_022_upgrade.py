#!/usr/bin/env python3
"""Actual offline opkg upgrade: published 0.2.1 -> 0.2.2 test IPK.

Never touches a receiver. Verifies old user data and the merged current plugin
payload including navigation, screensaver, original artwork cache and branding.
"""
import argparse
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from WarderRadio.warder_update import _control_archive

PACKAGE='enigma2-plugin-extensions-radio-warder-evolution'
DIR='usr/lib/enigma2/python/Plugins/Extensions/WarderRadio'

def fields(ipk):
    with tarfile.open(fileobj=io.BytesIO(_control_archive(ipk)), mode='r:*') as archive:
        data=archive.extractfile('./control').read().decode('utf-8')
    return {k.strip():v.strip() for line in data.splitlines() if ':' in line
            for k,v in [line.split(':',1)]}

def run(opkg,stable,candidate):
    prior=fields(stable); latest=fields(candidate)
    assert prior['Package']==latest['Package']==PACKAGE
    assert prior['Version']=='0.2.1-1',prior['Version']
    assert latest['Version']=='0.2.2-1',latest['Version']
    expected=json.loads((ROOT/'dist/build.json').read_text())
    assert expected['version']=='0.2.2-1'
    assert expected['file']==candidate.name
    assert candidate.stat().st_size<10_000_000,'IPK must not embed 40k global country logos'
    import hashlib
    assert hashlib.sha256(candidate.read_bytes()).hexdigest()==expected['sha256']
    dependencies={v.strip() for item in (prior,latest)
                    for v in item.get('Depends','').split(',') if v.strip()}
    with tempfile.TemporaryDirectory(prefix='warder-full-022-test-') as temp:
        root=Path(temp);info=root/'var/lib/opkg/info';info.mkdir(parents=True)
        status=root/'var/lib/opkg/status'
        status.write_text(''.join('Package: '+v+'\nVersion: 1.0\nArchitecture: all\n'
                     'Status: install ok installed\n\n' for v in sorted(dependencies)))
        for dependency in dependencies:(info/(dependency+'.list')).touch()
        config=root/'opkg.conf'
        config.write_text('dest root /\narch all 1\noption info_dir /var/lib/opkg/info\n'
                          'option status_file /var/lib/opkg/status\n')
        def install(path,reinstall=False):
            args=[str(opkg),'-o',str(root),'-f',str(config),'--force-postinstall']
            if reinstall:args.append('--force-reinstall')
            process=subprocess.run(args+['install',str(path)],text=True,capture_output=True,
                                   env={**os.environ,'IPKG_INSTROOT':str(root)})
            if process.returncode:
                raise AssertionError(process.stdout+'\n'+process.stderr)
        install(stable)
        plugin=root/DIR
        assert (plugin/'version.txt').read_text().strip()=='0.2.1'
        assert (plugin/'plugin.py').exists()
        user=root/'etc/enigma2/warder-radio'
        station={'name':'Testové rádio','url':'https://radio.example.org/live','group':'Slovensko'}
        state={
            'favourites':[station],
            'history':[station],
            'custom':[dict(station,name='Moje rádio',group='Custom')],
            'show_main_menu':True,
            'screensaver_delay':20,
            'online_country':'SK',
            'group':'Slovensko',
        }
        preserved={
            user/'state.json':json.dumps(state,ensure_ascii=False).encode(),
            user/'picon-settings.json':b'{"style":"black"}',
            user/'catalogue.json':b'{"saved":true}',
            user/'station-logo-cache/custom.png':b'user-added-logo-stays',
            root/'media/hdd/picon/radio/custom.png':b'user-custom-picon-stays',
            root/'media/hdd/WarderRadio/test-recording.mp3':b'user recording must remain',
        }
        for path,raw in preserved.items():
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        install(candidate)
        for p,v in preserved.items():assert p.read_bytes()==v,str(p)
        assert (plugin/'version.txt').read_text().strip()=='0.2.2'
        for file in ('screensaver.py','radio_browser.py','station_logos.py',
                     'curated_station_logos.py','homepage_logos.py','logo_source_guard.py',
                     'svg_logos.py','settings_screen.py','plugin.py','screen.py',
                     'recording.py','warder_update.py'):
            assert (plugin/file).is_file(),file
        code=(plugin/'plugin.py').read_text()
        assert 'show_main_menu' in code and 'WHERE_MENU' in code
        store_cmd=('from WarderRadio.model import Store; import sys; s=Store(sys.argv[1]); '
                   'assert s.show_main_menu and s.screensaver_delay==20; '
                   'assert len(s.favourites)==len(s.history)==len(s.custom)==1')
        subprocess.run([sys.executable,'-c',store_cmd,str(user)],check=True,cwd=root,
                      env={**os.environ,'PYTHONPATH':str(plugin.parent),'PYTHONDONTWRITEBYTECODE':'1'})
        install(candidate,reinstall=True)
        for p,v in preserved.items():assert p.read_bytes()==v,str(p)
        print('OFFLINE OPKG 0.2.1-1 -> 0.2.2-1 + reinstall: PASS')
        print('Runtime screensaver / menu / latest station logo recovery payload: PASS')
        print(str(len(preserved))+' persistent settings, favourites, history, picons and recordings byte-identical: PASS')
        print('Test-only installation; no production release/feed update: PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--opkg',required=True,type=Path)
    p.add_argument('--stable',required=True,type=Path)
    p.add_argument('--candidate',required=True,type=Path)
    a=p.parse_args()
    run(a.opkg.resolve(),a.stable.resolve(),a.candidate.resolve())
