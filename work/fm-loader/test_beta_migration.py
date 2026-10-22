"""Execute the installer's real migration body against stale and live fixtures."""
import pathlib, tempfile, subprocess, os, re
P=pathlib.Path(__file__).resolve().parent
s=(P/'Install-FM.ps1').read_text(encoding='utf-8-sig')
assert '# BEGIN FM BETA MIGRATION' in s,'Explicit beta migration is missing'
body=s.split('# BEGIN FM BETA MIGRATION',1)[1].split('# END FM BETA MIGRATION',1)[0]
assert not re.search(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*(?=\s)',body),'No recursive removal during migration'
assert 'pm clear' not in body and 'pm uninstall' not in s and 'uninstall ' not in s
assert 'stopservice' not in body and 'force-stop' not in body
with tempfile.TemporaryDirectory(prefix='fm-beta-migrate-') as temp:
 d=pathlib.Path(temp);(d/'mailbox').mkdir();(d/'runtime').mkdir()
 stale=['mailbox/request','mailbox/request.tmp','mailbox/online','mailbox/old-token.reply','broker.pid','config.next','reply.new','reply.body','runtime/ready-333','runtime/used-333','runtime/reloaded-333','runtime/error-333']
 keep=['active','config.xml','operation.lock','broker.lock','capture.log','capture.log.1','session-previous.txt','session-start.txt','runtime/ready-444','runtime/used-444','runtime/reloaded-444','runtime/error-444','runtime/unrelated','mailbox/unrelated']
 for name in stale+keep:(d/name).write_text('SENTINEL '+name,encoding='utf8')
 env=os.environ.copy();env['FM_TEST_MIGRATION_DIR']=str(d).replace('\\','/')
 script='D="$FM_TEST_MIGRATION_DIR"\npidof() { echo 444; }\n'+body
 for attempt in range(2):
  r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=script.encode(),env=env,capture_output=True)
  assert r.returncode==0,(r.stdout,r.stderr)
  assert all(not (d/n).exists() for n in stale),[n for n in stale if (d/n).exists()]
  assert all((d/n).read_text(encoding='utf8')=='SENTINEL '+n for n in keep)
 print('PASS real beta migration removes stale mailbox/dead markers, preserves active adapter/logs/locks/boot evidence, repeat-safe')
