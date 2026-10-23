# Сборщик отчёта FM и пробуждения для Windows

[Скачать Voyah-FM-PC-Collect-3.zip](https://github.com/kirbush/VoyahFree-SportPlus-radio-resurrection/raw/refs/heads/main/downloads/Voyah-FM-PC-Collect-3.zip)

1. Распаковать архив целиком. В персональном пакете отправка уже настроена; для публичного upload.json предоставляется отдельно.
2. После возврата к машине снять заставку до подключения ПК, частоту пока не менять.
3. Подключить ПК по USB, запустить Collect-FM-now.cmd и выбрать папку.
4. Дождаться COLLECT_OK и UPLOAD_SENT, затем отключить USB. Копия ZIP остаётся на ПК.

Collector3 дополнительно читает существующие OEM power/bootcontrol/UART журналы,
состояние питания и процессов, хеши штатных компонентов и suspend counters.
Исторические кольца читаются до медленных снимков; запись на ГУ не останавливается.
Команд настройки/перезапуска FM, изменения питания или установки APK нет.
Сбор до четырёх минут; при отсутствии root отчёт явно ограничен.

Публичный архив без действующих ключей. Ошибка отправки сохраняет ZIP и очередь.

Размер: 3221050 байт. SHA256: `b4b1bb0416f2ed1e5bbcfb5dadb7ba3f2ef1bc1894442613dfdb71daa6422a6a`.

[Прежний Collect-2](https://github.com/kirbush/VoyahFree-SportPlus-radio-resurrection/raw/refs/heads/main/downloads/Voyah-FM-PC-Collect-2.zip) и [Collect-1](https://github.com/kirbush/VoyahFree-SportPlus-radio-resurrection/raw/refs/heads/main/downloads/Voyah-FM-PC-Collect-1.zip) сохранены. Установщик FM0.5.1 остаётся прежним.
