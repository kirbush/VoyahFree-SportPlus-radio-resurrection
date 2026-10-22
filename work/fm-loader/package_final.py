import pathlib,zipfile,hashlib,json,subprocess
P=pathlib.Path(__file__).resolve().parent;W=P.parent;O=W.parent/'outputs'
A=O/'Voyah-FM-Tester-0.3.apk';sha=lambda b:hashlib.sha256(b).hexdigest()
tests=json.loads((W/'fm-loader-validation/offline-0.3-tests.json').read_text(encoding='utf8'));assert all(t['code']==0 for t in tests.values())
with zipfile.ZipFile(A) as z:
 assert z.testzip() is None
 for f in (P/'assets').iterdir():
  if f.is_file():assert z.read('assets/'+f.name)==f.read_bytes(),f.name
 assert z.read('classes.dex')==(P/'build/dex/classes.dex').read_bytes()
 members={n:sha(z.read(n)) for n in ['classes.dex','AndroidManifest.xml',*['assets/'+f.name for f in (P/'assets').iterdir() if f.is_file()]]}
(W/'fm-loader-validation/final-0.3-apk-members.json').write_text(json.dumps(members,indent=2))
validation='''VOYAH FM TESTER0.3 — ГРАНИЦЫ ПРОВЕРКИ
22.10.2026

Прошли12 групп автоматических проверок без автомобиля:
- Контракты запрета записи firmware и пересоздания DABService.
- Реальная ветка установки компонентов: уже есть/нет/частичный набор/отказ подписи/API/SELinux.
- Исчезновение аппаратных дескрипторов не маскируется READY_ALREADY_ACTIVE.
- Восемь одновременных запросов UI/службы получают свои ответы.
- ZIP/заметки кириллицей/логи приложения/ограниченный отчёт при отсутствии root.
- Выгрузка через настоящий WindowsPowerShell: root-adbd безsu, su0, общая память,
  двоичная целостность, коллизии имён, несколько устройств, неверный SHA и неполный ZIP.
- Настоящий Windows-установщик с имитацией ADB: root-adbd, su0 с правильным владельцем
  каталога загрузки, отсутствующий root, другой API, Enforcing, отказ установки,
  отсутствие USB-оборудования, отсутствие/несколько/неавторизованное устройство.
- JS-адаптер: значения конфигурации, некорректные параметры, несколько экземпляров,
  позднее появление службы и освобождение ресурсов; нет вызовов её lifecycle.
- Синтаксис helper.sh/broker.sh; генерируемый установщиком bootstrap.sh.
- Повторные попытки при позднем root/долгом отсутствии оборудования, сброс задержки.
- Telnet negotiation, отклонение эха маркера и ненулевого результата команды.

Оригинальная машина: пользователь подтвердил ровный FM через адаптер предыдущей0.2;
обычный UID10057 самостоятельно активировал root-посредника, записал свежий лог и ZIP.
Полная0.3 после изменений UI/IPC/retry/installer на автомобиле ещё не выполнялась.
Нельзя называть её проверенной живой установкой на7.3.1 или после полного reboot.

По фактическому образу731 проверены API30, kernelUSBdrivers, Permissivecommandline,
подписи, отсутствие Adayo/RDS/config, общаяаудиослужба, выбранные Binder/API-классы,
обязательные ARM64nativeimports. По ОД13.1 извлечены оригинальные FM-компоненты.
Подробности в приложенных отчётах об образах.

Независимая проверка кода нашла и помогла исправить пропуск hardware_ready в быстром
пути и владельца staging-каталога при su0 fallback. Приёмка нового root-adbd пути
выгрузки проверена отдельным тестом. Неизвестный холодный случай: если дефолтная
карта2 успела успешно открыться как другое capture-устройство, изменение поля
конфигурации уже открытый PCM не переключает. Первый hardware_ready в этом случае
отклонит запуск. Пересоздание службы не добавлялось. Проверяется живым тестом.

Критерий завершения испытания: звук/переключение/возврат после музыки и повторный
запуск после полного reboot без ПК при исправном Tweaks, затем сон/пробуждение.
Сейчас готовы установщик и тестовый комплект для такой проверки; результат не обещан.
'''
validation+='\nAPK SHA256: '+sha(A.read_bytes())+'\n'
(O/'Voyah-FM-Tester-0.3-VALIDATION.txt').write_text(validation,encoding='utf-8-sig')
files={
 'Voyah-FM-Tester-0.3.apk':A,
 'Install-FM.cmd':P/'Install-FM.cmd', 'Install-FM.ps1':P/'Install-FM.ps1',
 'ИНСТРУКЦИЯ.txt':P/'TESTER-START-HERE.txt',
 'Details/TECHNICAL-NOTES.txt':P/'TESTER-TECHNICAL-NOTES.txt',
 'Details/VALIDATION.txt':O/'Voyah-FM-Tester-0.3-VALIDATION.txt',
 'Details/Firmware-check-7.3.1.txt':O/'Voyah-FM-7.3.1-image-check.txt',
 'Details/Stock-radio-OD13.1.txt':O/'Voyah-FM-OD13.1-comparison.txt',
 'PC-Export/Export-FM-logs.cmd':P/'Export-FM-logs.cmd',
 'PC-Export/Export-FM-logs.ps1':P/'Export-FM-logs.ps1',
}
for n in ['adb.exe','AdbWinApi.dll','AdbWinUsbApi.dll','NOTICE.txt']:files['adb/'+n]=W/'installer/package/adb'/n
hashes={n:sha(f.read_bytes()) for n,f in files.items()}
(O/'Voyah-FM-Tester-0.3-hashes.json').write_text(json.dumps(hashes,indent=2))
target=O/'Voyah-FM-Tester-0.3-simple.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,f in files.items():z.write(f,n)
 z.writestr('SHA256.json',json.dumps(hashes,indent=2))
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 assert set(z.namelist())==set(files)|{'SHA256.json'}
 for n,h in hashes.items():assert sha(z.read(n))==h
 assert z.read('Install-FM.ps1').startswith(b'\xef\xbb\xbf')
 assert z.read('PC-Export/Export-FM-logs.ps1').startswith(b'\xef\xbb\xbf')
result=dict(archive=str(target),bytes=target.stat().st_size,sha256=sha(target.read_bytes()),apkSha256=hashes[A.name],entries=len(files)+1,offlineGroups=len(tests))
(O/'Voyah-FM-Tester-0.3-release.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
