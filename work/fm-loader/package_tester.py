"""Package the already-tested tester without a device connection."""
import pathlib,zipfile,hashlib,json,shutil
P=pathlib.Path(__file__).resolve().parent; W=P.parent; O=P.parents[1]/'outputs';V=W/'fm-loader-validation'
apk=O/'Voyah-FM-Tester-0.2.apk'
tested=json.loads((V/'tested-apk-members.json').read_text())
with zipfile.ZipFile(apk) as z:
 assert z.testzip() is None
 for name,digest in tested.items():
  assert hashlib.sha256(z.read(name)).hexdigest()==digest, 'Tested APK member changed: '+name
 for name in ['helper.sh','broker.sh','adapter.js','template.xml','frida-inject','AdayoDAB.apk','RdsApp.apk']:
  assert z.read('assets/'+name)==(P/'assets'/name).read_bytes(),name
 assert z.read('assets/Frida-LICENSE.txt')
 assert z.read('assets/LGPL-2.0.txt')
readme='''VOYAH FM TESTER 0.2 — ИНСТРУКЦИЯ ДЛЯ ПРОВЕРКИ
22 октября 2026 года

Для Voyah Free с китайской прошивкой и установленным Tweaks.
Это тестовая сборка восстановления аналогового FM. На исходной российской прошивке проверены адаптер, ровное воспроизведение, самостоятельный запуск root-посредника, запись логов и создание ZIP. На китайской прошивке совместимость ещё НЕ подтверждена.

ПОДГОТОВКА
Установить Voyah-FM-Tester-0.2.apk как обычное Android-приложение на головное устройство. В меню оно называется «Voyah FM Tester». Компьютер для обычной проверки не нужен, если в этой системе доступен совместимый локальный root-канал.
Первую проверку выполнять на стоянке. Автозапуск после перезагрузки пока оставить выключенным.

ПОРЯДОК ПРОВЕРКИ
1. Нажать «1. Проверить совместимость».
   Отсутствие FM-пакетов (MISSING_PACKAGE) на китайской прошивке ожидаемо: сборка содержит сохранённые оригинальные компоненты.
   При сообщениях о неизвестном APK, неподдержанном Android, SELinux или недоступном root сохранить отчёт и прислать его для разбора. Защиты и прошивку вручную менять не требуется.
2. Нажать «2. Начать запись логов».
3. Нажать «3. Установить и запустить FM». Приложение устанавливает только отсутствующие оригинальные FM-пакеты в /data. Существующие пакеты не заменяет; штатная проверка подписи Android действует.
4. Нажать «Открыть радио». Если оно открылось, выбрать заведомо работающую местную частоту. Послушать 1–2 минуты, переключить станцию и вернуться обратно. Отметить, есть ли звук, обрывы, обновляется ли название станции.
5. По возможности включить музыку из другого приложения, затем вернуться к FM: проверить переключение источников и возврат звука.
6. Вернуться в Voyah FM Tester и нажать «Остановить запись логов».
7. Вписать в поле отчёта точную версию китайской прошивки, частоту, результат и примерное время сбоя.
8. Нажать «4. Сохранить отчёт ZIP», выбрать, например, папку Downloads и подтвердить сохранение. Передать полученный Voyah-FM-report-ДАТА-ВРЕМЯ.zip для анализа, даже если радио не запустилось.

ЕСЛИ НИЧЕГО НЕ ЗАПУСКАЕТСЯ
Кнопка сохранения отчёта работает и при недоступном root: в ZIP сохранятся доступные сведения и причина отказа. Приложение не отправляет логи автоматически.
При недоступном root не нужно перебирать команды или менять SELinux. Достаточно прислать ZIP: способ доступа и ограничения проверим по фактической системе.

ЧТО ДЕЛАЕТ СБОРКА
Проверяет USB-тюнер и USB-аудио, версии и контрольные суммы FM-компонентов. Применяет номер звуковой карты и путь UART к существующей конфигурации FM-службы без её пересоздания. Не запускает второй поток чтения камер/аудио и не отправляет команды движения автомобиля.
Компоненты хранятся в /data, файлы system/vendor/boot и автозапуск Tweaks не изменяются. Собственная копия вспомогательного инструмента не заменяет файлы Tweaks.
Запись логов кольцевая и ограничена по размеру. ZIP содержит модель/сборку системы, USB/аудио, состояния служб, ошибки установки и FM-логи.

АВТОЗАПУСК И ВЫКЛЮЧЕНИЕ
Галочку запуска после перезагрузки проверять после успешного первого теста. Автозапуск реализован, но полной перезагрузкой пока не проверен; на другой прошивке он зависит от фактически доступного root-канала.
«Выключить адаптер» останавливает контроль адаптера. Применённые параметры остаются в памяти текущей FM-сессии до завершения её процесса или перезагрузки.
Удаление Voyah FM Tester не удаляет отдельно установленные FM-компоненты. Если тест неудачен, сначала сохранить ZIP, выключить адаптер и оставить автозапуск выключенным.

СОСТАВ И ПРАВА
В APK включены сохранённые оригинальные AdayoDAB/RdsApp с исходными подписями и Frida16.5.9. Права на штатные автомобильные APK принадлежат их разработчикам. Лицензии вспомогательного инструмента находятся в assets APK.
'''
validation='''VOYAH FM TESTER 0.2 — ПРОВЕРЕННЫЙ ОБЪЁМ

Проверено на исходном ГУ Android11/API30/build650, с Tweaks и уже существовавшим локальным vendor-root-каналом.
1. Адаптер применяет поля существующего объекта конфигурации; один PcmPlayThread. PID21622 сохранился при выключении/повторном включении/повторном запуске.
2. Пользователь подтвердил ровное FM-воспроизведение после устранения накопленных PCM-потоков раннего прототипа.
3. В измеренном интервале PID/один PCM-поток стабильны, кадры AudioTrack продвигались, счётчик underruns не рос:3200→3200.
4. После остановки старого root-посредника инструментальный тест выполнялся от обычного UID10057. Приложение самостоятельно активировало нового посредника через уже существующий loopback-канал, без запуска su от имени приложения.
5. Проверка устройств, log-start, запись контрольного нового события, log-stop и создание ZIP прошли. В ZIP найдено именно новое записанное событие; CRC всех файлов проверен.
6. Android разрешает стандартный ACTION_CREATE_DOCUMENT для application/zip через DocumentsUI. Сохранение использует системный выбор папки. Нажатия сохранения через этот интерфейс вручную не тестировались.
7. JVM-тест протокола: telnet negotiation, исключение эха команды из признака успеха, обработка ненулевого кода.
8. Проверки конфигурации: динамические card/port, отказ при некорректных значениях и неоднозначной службе. Проверки обнаружения: другой номер card/tty, отсутствующие/неверные/дублирующиеся USB IDs.
9. Проверки единственного адаптера учитывают настоящий /proc/PID/exe и argv, оставляют чужие процессы нетронутыми. Проверки запрета пересоздания DABService/записи firmware и контрольных сумм шаблона/APK проходят.
10. Итоговая APK-подпись проверена. После добавления лицензий classes.dex, манифест и весь исполняемый payload побайтно соответствуют прошедшей проверку сборке.

Не проверено: работа на китайской7.3.0, установка этих FM-пакетов при их отсутствии на целевом ГУ, целевая платформенная подпись/библиотеки/qg.audio_policy, полный reboot, итоговое переключение аудиофокуса на целевой машине. Никакой гарантии работы7.3.0 эти испытания не дают.
Сессия с автомобилем завершилась из-за разряда ноутбука. Финальная упаковка и проверка идентичности исполняемых файлов выполнены без нового подключения к машине.
'''
(O/'Voyah-FM-Tester-0.2-README.txt').write_text(readme,encoding='utf-8-sig')
(O/'Voyah-FM-Tester-0.2-VALIDATION.txt').write_text(validation,encoding='utf-8-sig')
shutil.copyfile(P/'Activate-FM.ps1',O/'Activate-FM.ps1')
names=['Voyah-FM-Tester-0.2.apk','Voyah-FM-Tester-0.2-README.txt','Voyah-FM-Tester-0.2-VALIDATION.txt']
hashes={n:{'bytes':(O/n).stat().st_size,'sha256':hashlib.sha256((O/n).read_bytes()).hexdigest()} for n in names}
(O/'Voyah-FM-Tester-0.2-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
package=O/'Voyah-FM-Tester-0.2-package.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in [*names,'Voyah-FM-Tester-0.2-hashes.json']:z.write(O/name,name)
with zipfile.ZipFile(package) as z:
 assert z.testzip() is None
 for name,record in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==record['sha256']
source=O/'Voyah-FM-Tester-0.2-source.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in ['AndroidManifest.xml','build.py','Activate-FM.ps1','test_adapter.js','test_contract.py','test_discovery_device.py','test_injector_device.py']:
  z.write(P/name,'fm-loader/'+name)
 for folder in ['src','assets','tests','licenses']:
  for f in (P/folder).rglob('*'):
   if f.is_file():z.write(f,'fm-loader/'+f.relative_to(P).as_posix())
 z.write(O/'Voyah-FM-Tester-0.2-VALIDATION.txt','VALIDATION.txt')
with zipfile.ZipFile(source) as z:assert z.testzip() is None
print(json.dumps({'files':hashes,'package_bytes':package.stat().st_size,'source_bytes':source.stat().st_size},indent=2))
