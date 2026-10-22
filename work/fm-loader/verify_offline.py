import pathlib,subprocess,sys,json,concurrent.futures,tempfile
p=pathlib.Path(__file__).resolve().parent;w=p.parent;out=w/'fm-loader-validation';out.mkdir(exist_ok=True)
node=pathlib.Path(r'C:/Users/Кирилл/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
commands={n:[sys.executable,str(p/n)] for n in ['test_contract.py','test_install_offline.py','test_health_offline.py','test_mailbox_offline.py','test_reports_offline.py','test_pc_export.py','test_installer_offline.py','test_beta_offline.py','test_beta_lifecycle.py','test_beta_migration.py','test_scan_diagnostics.py','test_installer_fd_compat.py','test_android_payload_format.py']}
commands['test_pc_collect.py']=[sys.executable,str(p/'test_pc_collect.py')]
commands['test_upload_receiver.py']=[sys.executable,str(p/'tests/test_upload_receiver.py')]
commands['test_upload_pc.py']=[sys.executable,str(p/'tests/test_upload_pc.py')]
commands['test_android_upload.py']=[sys.executable,str(p/'test_android_upload.py')]
commands['test_upload_config_install.py']=[sys.executable,str(p/'test_upload_config_install.py')]
commands['test_ui_helper.py']=[sys.executable,str(p/'test_ui_helper.py')]
commands['ui-adapter']=[str(node),str(p/'test_ui_adapter.js')]
commands['adapter']=[str(node),str(p/'test_adapter.js')]
commands['helper-syntax']=['C:/Program Files/Git/bin/bash.exe','-n',str(p/'assets/helper.sh')]
commands['broker-syntax']=['C:/Program Files/Git/bin/bash.exe','-n',str(p/'assets/broker.sh')]
def run(item):
 n,c=item
 try:r=subprocess.run(c,capture_output=True,timeout=300 if n=='test_installer_offline.py' else 150)
 except subprocess.TimeoutExpired as error:return n,dict(code=124,output='Test group timeout: '+n)
 return n,dict(code=r.returncode,output=(r.stdout+r.stderr).decode('utf8',errors='replace'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(run,commands.items()))
j=w/'toolchains/jdk/jdk-17.0.21-lite/bin'
with tempfile.TemporaryDirectory(prefix='fm-jvm-final-') as td:
 src=p/'src/ru/local/voyah/fmloader'
 subprocess.run([str(j/'javac.exe'),'--release','8','-d',td,str(src/'RetrySchedule.java'),str(src/'TelnetSession.java'),str(p/'tests/TestRetrySchedule.java'),str(p/'tests/TestTelnetSession.java')],check=True)
 for cls in ['ru.local.voyah.fmloader.TestRetrySchedule','TestTelnetSession']:
  r=subprocess.run([str(j/'java.exe'),'-cp',td,cls],capture_output=True,timeout=20);results[cls]=dict(code=r.returncode,output=(r.stdout+r.stderr).decode())
(out/'offline-0.5.1-tests.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf8')
for n,r in results.items():print(('PASS ' if r['code']==0 else 'FAIL ')+n,flush=True)
assert all(r['code']==0 for r in results.values()),json.dumps(results,ensure_ascii=False)
