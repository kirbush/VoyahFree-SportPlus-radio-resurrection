"""Execute the installer's emitted private-config body, without ADB or networking."""
import pathlib,tempfile,subprocess,os,json
P=pathlib.Path(__file__).resolve().parent
source=(P/'Install-FM.ps1').read_text(encoding='utf-8-sig')
body=source.split('# BEGIN FM UPLOAD CONFIG',1)[1].split('# END FM UPLOAD CONFIG',1)[0]
with tempfile.TemporaryDirectory(prefix='fm-private-config-') as temp:
 t=pathlib.Path(temp);files=t/'private files';files.mkdir();stage=t/'upload';stage.mkdir()
 config={'endpoint':'https://example.invalid/voyah-fm/v1','client':'owner-01','token':'local_only_test_token_'+'x'*32}
 (stage/'upload.json').write_text(json.dumps(config),encoding='utf8')
 (files/'upload.json').write_text('old config',encoding='utf8')
 keep=['Voyah-FM-report-20261022-170000.zip','events.log','stations-sentinel']
 for name in keep:(files/name).write_text('SENTINEL '+name)
 env=os.environ.copy();env.update(FM_TEST_FILES=str(files).replace('\\','/'),FM_TEST_STAGE=str(stage).replace('\\','/'))
 script='''set -e
umask 077
uid=12345
S="$FM_TEST_STAGE"
chown() { printf 'OWNER %s\\n' "$*"; }
chmod() { printf 'MODE %s\\n' "$*"; }
restorecon() { :; }
mv() { printf 'RENAME %s\\n' "$*"; command mv "$@"; }
'''+body.replace('F=/data/user/0/ru.local.voyah.fmloader/files','F="$FM_TEST_FILES"')
 r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=script.encode(),env=env,capture_output=True,check=True)
 output=r.stdout.decode('utf8');assert config['token'] not in output
 assert json.loads((files/'upload.json').read_text())==config
 assert 'OWNER 12345:12345 ' in output and 'MODE 600 ' in output
 assert output.index('MODE 600 ')<output.index('RENAME ')
 assert not (files/'.upload.json.install').exists()
 for name in keep:assert (files/name).read_text()=='SENTINEL '+name
 print('PASS actual private-config install: atomic replacement, app UID/0600 before rename, reports preserved, no token output')
