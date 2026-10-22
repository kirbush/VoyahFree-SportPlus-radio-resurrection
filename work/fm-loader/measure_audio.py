import pathlib,subprocess,time,json,re
A='C:/Users/Кирилл/Downloads/ADB_AppControl/adb/adb.exe';O=pathlib.Path('work/fm-loader-validation')
def shell(command):return subprocess.run([A,'-s','35be55ef','shell',command],capture_output=True,timeout=30).stdout.decode(errors='replace')
def snap(name):
 pid=shell('pidof com.adayo.service.dab').strip()
 script='p=$(pidof com.adayo.service.dab); for t in /proc/$p/task/*/comm; do cat "$t"; done\n'
 t=subprocess.run([A,'-s','35be55ef','shell','su','0','sh'],input=script.encode(),capture_output=True,timeout=15).stdout.decode(errors='replace')
 audio=shell('dumpsys media.audio_flinger');(O/(name+'-audio.txt')).write_text(audio,encoding='utf-8')
 tracks=[l.strip() for l in audio.splitlines() if re.match(r'\s+\d+\s+(?:yes|no)\s+'+pid+r'\s+',l)]
 r={'pid':pid,'pcm_threads':t.splitlines().count('PcmPlayThread'),'tracks':tracks,'time':time.time()}
 (O/(name+'.json')).write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r),flush=True);return r
x=snap('inplace-interval-start');time.sleep(20);y=snap('inplace-interval-end')
assert x['pid']==y['pid'] and x['pcm_threads']==y['pcm_threads']==1
print('PASS stable process and one PCM reader over20seconds')
