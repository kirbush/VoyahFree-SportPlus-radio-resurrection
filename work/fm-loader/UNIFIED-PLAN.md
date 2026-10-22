# 0.5.0-beta / одно приложение, 22.10.2026

Пользователь передал два новых отчёта, просит новый установщик, одно приложение с меню настроек на штатном экране и отправкой логов. Затем явно разрешил установить на собственное подключённое ГУ. Кнопку отправки на его ГУ пользователь нажмёт сам; агент её не нажимает и реальный отчёт с этого ГУ до нажатия не отправляет.

## Установленные факты

- PC ZIP 205120: SHA256 27b4c8ebf230acf6bd2b50e7708763b765bfe95ec20bb4fdb1202bb0421b954f, 195729 bytes. Android11 OTA7.2/build18. RdsApp падает 18:58:47.594: IllegalStateException, DisplayUtils$1 observer already registered через MultiDisplayObservable/DisplayUtils.registerDisplayChange/MainActivity.onCreate delayed lambda.
- Тот же PC снимок: task517 с baseIntent/affinity FM Диагностики фактически содержит только RdsApp MainActivity, launchedFromPackage=fmloader. Отдельный экран диагностики отсутствует; диагностику не объявлять падающей без исключения. Меню внутри RDS избегает этого перехода задач.
- App ZIP215323: SHA256 d4a8b9ed0c3abc01ddd5c732e86457d147a598930981cc94075f5d429c4f2445, 11786 bytes, прежний первый тестер/build18. Есть новые BOOT_COMPLETED21:25 и21:52, transient serial_count0 перед вторым. Один PCM reader в последнем снимке. Старые падения RDS ещё в exit-info, нового стека в этом ZIP нет. Детальный разбор продолжить; сырые файлы вне Git в work/fm-report-analysis-2051-2153.
- Подключённое собственное ГУ serial35be55ef, Android11/API30, RUS H97x build650. ADB root получен. Наших APK пока нет; OEM RdsApp/Adayo присутствуют. Снимки до установки: work/fm-unified-device; не смешивать с отчётами тестеров/build18.

## Реализация и интерфейсы

- Версия0.5.0-beta, versionCode8, один наш APK FM Радио (прежний signer/package). Удалить только прежний ru.local.voyah.fmdiagnostics после успешной установки, сохранить станции/отчёты/native owner.
- Оригинальные OEM APK не менять/не переподписывать. Native Java UI bridge из assets/radio-ui.dex + короткий Frida assets/ui.js добавляет шестерёнку и AlertDialog на RdsApp MainActivity. Диалог не запускает другой Activity. UI callback-классы native Java, не Frida callbacks.
- ui.js отдельно от аппаратного adapter.js; отдельный selective injector identity -s ui.js, markers runtime/ui-ready-PID. Идемпотентный guard только повторного DisplayUtils$1 observer. Никаких Adayo lifecycle-команд, tune/scan/play.
- Штатный Intent запускается с NEW_TASK/CLEAR_TOP/SINGLE_TOP, чтобы не наследовать task диагностического экрана и не создавать новый экземпляр без необходимости.
- MenuActionReceiver (android:exported=true, android:permission=android.permission.DUMP): action ru.local.voyah.fmloader.REPORT_MENU, extra operation=status|send|save|auto_on|auto_off. Быстрый ordered broadcast ответ JSON без ключей: status, configured, auto, busy, version, lastReport. Не ждать отчёта внутри receiver.
- ReportCoordinator public static API: start(Context), command(Context,String)->JSONObject, isCapturing(), shutdown(). command(status) без root/network; send/save только очередь отдельного исполнителя. start — delayed periodic snapshot через30мин, без немедленной отправки при установке. Сбор логов по умолчанию остаётся включён. При capture health tick может пропустить проверку, сетевые запросы не блокируют hardware executor.
- Upload config: files/upload.json, HTTPS endpoint/client/token, владелец UID приложения,0600. Установщик -UploadConfig optional рядом с CMD; не печатать и не включать в public ZIP. Для собственного ГУ отдельный server client owner-01. Установщик не отправляет отчёт.
- Upload queue: SHA256 idempotency, bounded receipt, HTTPS validation/no redirects, local retry, исходные ZIP сохраняются. Только данные, без remote command endpoint. Кнопка save сохраняет ZIP в Downloads без external file-picker Activity.
- DiagnosticReport должен включать целевой crash buffer/DropBox из helper diagnostic, UI/boot/logger сведения, существующие события. Root script LF/noBOM. При экспорте не останавливать логирование.

## Проверка

Регрессии observer double registration, task isolation, UI menu operations; JVM queue/real transport+ack/offline/bounds, отсутствие hardware actions; fake-ADB новая/старая установка, приватная конфигурация и удаление старой диагностики; source/signedAPK LF guards; полный verify_offline + реальный архив installer.

После локальных проверок установить текущим installer с root/su на35be55ef, удостовериться, что один владелец hardware/PCM и UI меню доступно. Не нажимать send. Сообщить пользователю нажать кнопку; затем проверить app status/server receipt с его разрешённым действием.

## Границы параллельной работы

- Parent: report analysis; ui/MenuBridge.java, assets/ui.js, helper.sh, broker.sh, RuntimeFiles.java, MainActivity.java, AndroidManifest.xml, root docs/device installation.
- Android upload task: UploadQueue/ReportCoordinator/MenuActionReceiver.java, LoaderService.java, DiagnosticReport.java, новые upload/coordinator тесты. Не менять UI/installer/helper/manifest.
- Installer task: build_beta.py, package_beta.py, test_beta_package.py, Install-FM.ps1, LocalBootstrap.java; installer/migration/fakeADB tests и инструкции. UI dex собирается из src/ru/local/voyah/fmloader/ui/*.java в assets/radio-ui.dex. Не менять helper/UI/manifest/LoaderService/ReportCoordinator; не запускать реальный ADB.
