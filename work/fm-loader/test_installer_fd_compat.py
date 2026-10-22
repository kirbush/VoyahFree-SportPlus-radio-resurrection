"""Regression: simulate Android shell closing nonstandard FDs at exec boundary."""
import pathlib,tempfile,subprocess,os
P=pathlib.Path(__file__).resolve().parent
s=(P/'Install-FM.ps1').read_text(encoding='utf-8-sig')
acquire=s.split('# Keep advisory lock files: unlinking a locked inode would defeat serialization.',1)[1].split('# BEGIN FM BETA MIGRATION',1)[0]
with tempfile.TemporaryDirectory(prefix='fm-fd-compat-') as temp:
 t=pathlib.Path(temp);(t/'runtime').mkdir();(t/'bin').mkdir()
 # Real child process. Close FD9 as Android mksh does; inherited standard FD0 survives.
 flock=t/'bin/flock'
 flock.write_text('#!/usr/bin/env bash\nexec 9>&-\nfd=$2\nif ( : >&"$fd" ) 2>/dev/null; then exit 0; fi\necho "flock: Bad file descriptor" >&2\nexit 1\n',encoding='ascii')
 script=t/'migration.sh'
 script.write_text('D="$TEST_D"\nsleep() { :; }\n'+acquire+'\necho LOCK_ACQUIRED\nexec 0</dev/null\n',encoding='utf8')
 env=os.environ.copy();env['TEST_D']=str(t/'runtime').replace('\\','/')
 env['TEST_BIN']=str(t/'bin').replace('\\','/')
 prefix='export PATH="$(cygpath -u "$TEST_BIN")":$PATH; exec bash "$TEST_SCRIPT"'
 env['TEST_SCRIPT']=str(script).replace('\\','/')
 r=subprocess.run(['C:/Program Files/Git/bin/bash.exe','-c',prefix],env=env,capture_output=True,timeout=10)
 assert r.returncode==0 and b'LOCK_ACQUIRED' in r.stdout,(r.returncode,r.stdout,r.stderr[:1500])
 assert b'Bad file descriptor' not in r.stderr
 print('PASS actual installer lock body across child process that closes FD9; standard FD0 inherited')
