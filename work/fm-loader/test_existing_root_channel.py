"""Read-only identity probe of the head unit's existing boot-time loopback service."""
import subprocess,socket,time,pathlib,re
A='C:/Users/Кирилл/Downloads/ADB_AppControl/adb/adb.exe'
port=subprocess.check_output([A,'-s','35be55ef','forward','tcp:0','tcp:23'],text=True).strip()
try:
 with socket.create_connection(('127.0.0.1',int(port)),timeout=3) as s:
  s.settimeout(2);s.sendall(b"\r\necho __FM_PROBE_BEGIN__; id -u; echo __FM_PROBE_END__\r\n");out=bytearray();deadline=time.time()+8
  def one():
   b=s.recv(1)
   if not b:raise EOFError()
   return b[0]
  while time.time()<deadline:
   try:
    b=one()
    if b==255:
     c=one()
     if c in [251,252,253,254]:
      option=one()
      if c==251:s.sendall(bytes([255,254,option]))
      if c==253:s.sendall(bytes([255,252,option]))
     continue
    out.append(b)
    if re.search(rb'\n__FM_PROBE_BEGIN__\r?\n0\r?\n__FM_PROBE_END__',out):break
   except socket.timeout:continue
  text=out.decode(errors='replace');print(text)
  assert re.search(r'\n__FM_PROBE_BEGIN__\r?\n0\r?\n__FM_PROBE_END__',text)
  pathlib.Path('work/fm-loader-validation/existing-root-channel.txt').write_text(text,encoding='utf-8')
finally:subprocess.run([A,'-s','35be55ef','forward','--remove','tcp:'+port],check=True)
