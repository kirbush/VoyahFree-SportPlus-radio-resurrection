import pathlib,zipfile,hashlib,json,shutil
P=pathlib.Path(__file__).resolve().parent;O=P.parents[1]/'outputs'
for name in ['Export-FM-logs.ps1','Export-FM-logs.cmd']:shutil.copyfile(P/name,O/name)
readme='''ВЫГРУЗКА ОТЧЁТА VOYAH FM НА ПК

1. На ГУ в Voyah FM Tester нажать «Сохранить отчёт ZIP». Внутренняя копия отчёта создаётся до выбора папки Android. Для запасного способа чтения сохранить ZIP также в Downloads на ГУ.
2. Подключить ГУ к Windows-компьютеру по USB; USB-отладка должна быть разрешена.
3. Распаковать этот архив целиком. Export-FM-logs.cmd и Export-FM-logs.ps1 должны лежать рядом.
4. Запустить Export-FM-logs.cmd. Утилита найдёт ADB в своей папке, в Downloads/ADB_AppControl/adb или в PATH. Если не найдёт, предложит указать adb.exe.
5. После обнаружения ГУ и отчёта появится окно выбора ПАПКИ НА ПК. Выбрать нужную папку и подтвердить.

По умолчанию копируется последний созданный Voyah-FM-report-ДАТА-ВРЕМЯ.zip из внутренней папки приложения. Если она недоступна через ADB root, утилита проверит Download/Downloads/Documents в общей памяти ГУ. Поэтому сохранение в Downloads — удобный запасной вариант.
Выгрузка не создаёт новый диагностический отчёт и не останавливает запись: сначала сформировать ZIP на ГУ. Приложение и прошивка при выгрузке не изменяются.
Передача бинарная, без преобразования содержимого ZIP в текст. Проверяется структура ZIP и, когда ГУ предоставляет SHA256, совпадение контрольных сумм. Существующий файл на ПК сохраняется: повторная выгрузка получает суффикс -2, -3 и т.д.

ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ POWERSHELL
С выбором папки:
  .\Export-FM-logs.cmd
Все созданные отчёты:
  .\Export-FM-logs.cmd -AllReports
Без диалогов, в заранее указанную папку:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\Export-FM-logs.ps1 -Destination "D:\\Voyah\\FM logs"
С явным путём ADB и устройством:
  .\Export-FM-logs.cmd -Adb "C:\\ADB\\adb.exe" -Serial 35be55ef

Если подключено несколько устройств, нужно указать -Serial из списка adb devices. Если отчёт не найден, сначала сохранить его в Voyah FM Tester. Если утилита сообщает несовпадение контрольной суммы или обрыв передачи, готовый ZIP не сохраняется; можно повторить выгрузку.

ПРОВЕРКА
Проверено без автомобиля на Windows PowerShell5.1 с имитацией ADB: чтение внутренней/общей памяти, побайтное сохранение ZIP, папки с кириллицей и пробелами, повторная выгрузка, отсутствие устройства/отчёта, неверный SHA256 и ошибка передачи. ZIP проверен Python zipfile.testzip. Реальное подключение к ГУ для этой утилиты после разрыва автомобильной сессии ещё не проверено. Диалог выбора папки использует стандартный FolderBrowserDialog Windows; в автоматических тестах папка передавалась параметром.
'''
(O/'Export-FM-logs-README.txt').write_text(readme,encoding='utf-8-sig')
names=['Export-FM-logs.cmd','Export-FM-logs.ps1','Export-FM-logs-README.txt']
hashes={n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in names}
(O/'Export-FM-logs-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
with zipfile.ZipFile(O/'Export-FM-logs.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in [*names,'Export-FM-logs-hashes.json']:z.write(O/n,n)
with zipfile.ZipFile(O/'Export-FM-logs.zip') as z:assert z.testzip() is None
print(json.dumps({'bytes':(O/'Export-FM-logs.zip').stat().st_size,'files':hashes},indent=2))
