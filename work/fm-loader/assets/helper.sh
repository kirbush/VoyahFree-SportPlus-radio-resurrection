#!/system/bin/sh
# All writes are restricted to this private runtime directory in /data.
umask 077
D=/data/local/tmp/voyah-fm-loader-v1
AD=com.adayo.service.dab
RD=com.pateo.rdsapp
ADS=$AD/com.adayo.dab.DABService
RDS=$RD/com.pateo.midrds.media.RdsMediaBrowserService
fail() { echo "ERROR $*"; exit 1; }
[ "$(id -u)" = 0 ] || fail ROOT_REQUIRED
mkdir -p "$D/runtime"
chmod 755 "$D"
chown 1000:1000 "$D/runtime"
chmod 700 "$D/runtime"
exec 0>"$D/operation.lock"
chmod 600 "$D/operation.lock"
flock -n 0 || fail BUSY
verify() {
    pkg=$1; expected=$2
    path=$(pm path "$pkg" | head -1 | sed 's/^package://')
    [ -n "$path" ] || fail "MISSING_PACKAGE $pkg"
    got=$(sha256sum "$path" | cut -d' ' -f1)
    [ "$got" = "$expected" ] || fail "UNKNOWN_APK $pkg $got"
}
discover() {
    count=0; PORT=
    for tty in /sys/class/tty/ttyACM*; do
        [ -e "$tty/device" ] || continue
        parent=$(readlink -f "$tty/device")
        while [ "$parent" != / ] && [ -n "$parent" ]; do
            if [ -f "$parent/idVendor" ]; then
                if [ "$(cat "$parent/idVendor")" = 0483 ] && [ "$(cat "$parent/idProduct")" = 5740 ]; then
                    PORT=/dev/${tty##*/}; count=$((count+1))
                fi
                break
            fi
            parent=${parent%/*}; [ -n "$parent" ] || break
        done
    done
    [ "$count" = 1 ] || fail "AMBIGUOUS_USB serial_count=$count"
    count=0; CARD=
    for card in /proc/asound/card[0-9]*; do
        [ -f "$card/usbid" ] || continue
        if [ "$(cat "$card/usbid")" = 04fc:8005 ]; then CARD=${card##*card}; count=$((count+1)); fi
    done
    [ "$count" = 1 ] || fail "AMBIGUOUS_USB audio_count=$count"
    case "$CARD" in ''|*[!0-9]*) fail INVALID_CARD;; esac
    [ -c "$PORT" ] && [ -c "/dev/snd/pcmC${CARD}D0c" ] || fail DEVICE_MISSING
}
checks() {
    [ "$(getprop ro.build.version.sdk)" = 30 ] || fail UNTESTED_ANDROID_VERSION
    [ "$(getenforce)" = Permissive ] || fail SELINUX_POLICY_REQUIRED
    verify "$AD" dfafe5455ca9040306d012e3650df6181ab6e24d26f8bcaa9766a0cdc6d45905
    verify "$RD" 36b4d73a889aa78325f6a6ff0c8113c6b13605620a5a4b045209fbff36449cca
    discover
}
stop_injector() {
    for p in $(pidof frida-inject); do
        [ "$(readlink /proc/$p/exe 2>/dev/null)" = "$D/frida-inject" ] || continue
        cmd=$(tr '\000' ' ' < /proc/$p/cmdline 2>/dev/null)
        case "$cmd" in "frida-inject -p "*" -s $D/adapter.js"*|"$D/frida-inject -p "*" -s $D/adapter.js"*) kill "$p" 2>/dev/null;; esac
    done
    rm -f "$D/injector.pid"
}
hook_alive() {
    found=0
    for p in $(pidof frida-inject); do
        [ "$(readlink /proc/$p/exe 2>/dev/null)" = "$D/frida-inject" ] || continue
        cmd=$(tr '\000' ' ' < /proc/$p/cmdline 2>/dev/null)
        case "$cmd" in "frida-inject -p $pid -s $D/adapter.js"*|"$D/frida-inject -p $pid -s $D/adapter.js"*) found=$((found+1)); echo "$p" > "$D/injector.pid";; esac
    done
    [ "$found" = 1 ]
}
audio_threads() {
    count=0
    for t in /proc/$pid/task/*/comm; do
        [ "$(cat "$t" 2>/dev/null)" = PcmPlayThread ] && count=$((count+1))
    done
    echo "$count"
}
hardware_ready() {
    serialfd=0; pcmfd=0
    for fd in /proc/$pid/fd/*; do
        link=$(readlink "$fd" 2>/dev/null)
        [ "$link" != "$PORT" ] || serialfd=1
        [ "$link" != "/dev/snd/pcmC${CARD}D0c" ] || pcmfd=1
    done
    [ "$serialfd" = 1 ] && [ "$pcmfd" = 1 ] && [ "$(audio_threads)" = 1 ]
}
stop_log() {
    for p in $(pidof logcat); do
        cmd=$(tr '\000' ' ' < /proc/$p/cmdline 2>/dev/null)
        case "$cmd" in *" -f $D/capture.log "*) kill "$p" 2>/dev/null;; esac
    done
    rm -f "$D/recording"
}
scan_snapshot() {
    echo '=== SCAN / STATION LIST SNAPSHOT (READ ONLY) ==='
    # Exact original AIDL: 5=getFMStationList, 7=getFavoriteStations,
    # 8=getCurrentRadioStation. Never run these codes against another APK.
    if (verify "$AD" dfafe5455ca9040306d012e3650df6181ab6e24d26f8bcaa9766a0cdc6d45905); then
        for code in 5 7 8; do
            echo "READ_ONLY_BINDER adayo.dab transaction=$code"
            timeout 3 service call adayo.dab "$code" > "$D/scan-getter.tmp" 2>&1
            getter_status=$?
            echo "SCAN_GETTER_STATUS transaction=$code exit=$getter_status"
            head -c 65536 "$D/scan-getter.tmp"
            rm -f "$D/scan-getter.tmp"
            echo
        done
    else echo SCAN_SNAPSHOT_SKIPPED_UNKNOWN_APK; fi
    echo '=== RDS LIST FILTER / PLAY MODE ==='
    for prefs in /data/user/0/com.pateo.rdsapp/shared_prefs/*.xml; do
        [ -f "$prefs" ] || continue
        grep -H -E 'SP_PLAY_DATA|SP_PTY_STATE|playType|ptyCode' "$prefs" 2>/dev/null | head -c 16384
    done
    echo
}
ui_hook_alive() {
    ui_found=0
    for ui_p in $(pidof frida-inject); do
        [ "$(readlink /proc/$ui_p/exe 2>/dev/null)" = "$D/frida-inject" ] || continue
        ui_cmd=$(tr '\000' ' ' < /proc/$ui_p/cmdline 2>/dev/null)
        case "$ui_cmd" in "frida-inject -p $ui_pid -s $D/ui.js"*|"$D/frida-inject -p $ui_pid -s $D/ui.js"*)
            ui_found=$((ui_found+1)); echo "$ui_p" > "$D/ui-injector.pid";;
        esac
    done
    [ "$ui_found" = 1 ]
}
stop_ui_injector() {
    for ui_p in $(pidof frida-inject); do
        [ "$(readlink /proc/$ui_p/exe 2>/dev/null)" = "$D/frida-inject" ] || continue
        ui_cmd=$(tr '\000' ' ' < /proc/$ui_p/cmdline 2>/dev/null)
        case "$ui_cmd" in "frida-inject -p "*" -s $D/ui.js"*|"$D/frida-inject -p "*" -s $D/ui.js"*) kill "$ui_p" 2>/dev/null;; esac
    done
    rm -f "$D/ui-injector.pid"
}
ensure_ui() {
    verify "$RD" 36b4d73a889aa78325f6a6ff0c8113c6b13605620a5a4b045209fbff36449cca
    ui_pid=$(pidof "$RD")
    if [ -z "$ui_pid" ] && [ "$1" = explicit ]; then
        am startservice --user 0 -n "$RDS"
        for ui_n in 1 2 3 4 5; do ui_pid=$(pidof "$RD"); [ -n "$ui_pid" ] && break; sleep 1; done
    fi
    case "$ui_pid" in ''|*[!0-9]*) echo UI_WAIT_PROCESS; [ "$1" != explicit ]; return;; esac
    if ui_hook_alive && [ "$(cat "$D/runtime/ui-ready-$ui_pid" 2>/dev/null)" = 0.5.1-beta-v1 ]; then
        echo "UI_READY pid=$ui_pid"; return 0
    fi
    [ -f "$D/ui.js" ] && [ -f "$D/radio-ui.dex" ] || { echo UI_PAYLOAD_MISSING; return 1; }
    [ "$(sha256sum "$D/frida-inject" | cut -d' ' -f1)" = 0d99be0e44d4ca3449056fa0a0b868fca1cf66c8ad704508949945afc07706aa ] || { echo UI_INJECTOR_HASH_MISMATCH; return 1; }
    stop_ui_injector
    rm -f "$D/runtime/ui-ready-$ui_pid"
    nohup setsid "$D/frida-inject" -p "$ui_pid" -s "$D/ui.js" > "$D/ui-injector.log" 2>&1 < /dev/null &
    for ui_n in 1 2 3 4 5 6 7 8 9 10; do [ -f "$D/runtime/ui-ready-$ui_pid" ] && break; sleep 1; done
    [ "$(cat "$D/runtime/ui-ready-$ui_pid" 2>/dev/null)" = 0.5.1-beta-v1 ] && ui_hook_alive || { echo UI_NOT_READY; return 1; }
    echo "UI_READY pid=$ui_pid"
}
filter_fm_dropbox() {
    filter='
      BEGIN {matched=0}
      /^=/ {keep=0}
      /^[0-9][0-9][0-9][0-9]-/ {header=$0}
      /^DROPBOX_EXIT=/ {print;keep=0;next}
      /^Process:/ {
        keep=($0 ~ /^Process:[[:space:]]*(com\.pateo\.rdsapp|com\.adayo\.service\.dab|ru\.local\.voyah\.fmloader|ru\.local\.voyah\.fmdiagnostics)([[:space:],:]|$)/)
        if(keep){matched++;if(header!="")print header}
      }
      keep {print}
      END {if(!matched)print "NO_MATCHING_FM_CRASH_ENTRY"}
    '
    if command -v awk >/dev/null 2>&1; then awk "$filter"
    elif command -v busybox >/dev/null 2>&1; then busybox awk "$filter"
    else cat >/dev/null; echo CRASH_FILTER_UNAVAILABLE; fi
}
crash_snapshot() {
    echo '=== TARGETED CRASH TEXT / DROPBOX ==='
    timeout 4 logcat -b crash -d -v threadtime -t 600 > "$D/crash-buffer.tmp" 2>&1
    if command -v awk >/dev/null 2>&1; then
        awk 'NR==FNR {if($0 ~ /Process: (com\.pateo\.rdsapp|com\.adayo\.service\.dab|ru\.local\.voyah\.fmloader)(,|[[:space:]])/) own[$3]=1;next} own[$3]{print}' "$D/crash-buffer.tmp" "$D/crash-buffer.tmp" | tail -c 131072
    elif command -v busybox >/dev/null 2>&1; then
        busybox awk 'NR==FNR {if($0 ~ /Process: (com\.pateo\.rdsapp|com\.adayo\.service\.dab|ru\.local\.voyah\.fmloader)(,|[[:space:]])/) own[$3]=1;next} own[$3]{print}' "$D/crash-buffer.tmp" "$D/crash-buffer.tmp" | tail -c 131072
    else echo CRASH_FILTER_UNAVAILABLE; fi
    rm -f "$D/crash-buffer.tmp"
    for tag in system_app_crash data_app_crash; do
        echo "DROPBOX_TAG=$tag"
        { timeout 5 dumpsys dropbox --print "$tag"; echo "DROPBOX_EXIT=$?"; } 2>&1 | filter_fm_dropbox | tail -c 131072
    done
    echo '=== FM UI TASK / FOCUS ==='
    timeout 4 dumpsys activity activities 2>/dev/null | grep -E 'mResumedActivity|topResumedActivity|ResumedActivity:|taskAffinity=.*(rdsapp|fmloader|fmdiagnostics)|mActivityComponent=.*(rdsapp|fmloader|fmdiagnostics)|launchedFromUid.*(rdsapp|fmloader|fmdiagnostics)' | head -c 32768
    echo '=== UI ADAPTER ==='
    cat "$D/ui-injector.pid" 2>/dev/null
    tail -c 16384 "$D/ui-injector.log" 2>/dev/null
    echo
}
case "$1" in
ui-start)
    ensure_ui explicit || fail UI_NOT_READY
    ;;
check|status)
    checks
    pid=$(pidof "$AD")
    echo "CHECK_OK serial=$PORT audio_card=$CARD pid=$pid"
    if [ -n "$pid" ] && [ -f "$D/runtime/used-$pid" ] && [ -f "$D/active" ] && hook_alive && hardware_ready; then
        echo ADAPTER_ACTIVE
    else echo ADAPTER_INACTIVE; fi
    cat "/proc/asound/card$CARD/stream0"
    ;;
start)
    checks
    [ "$(sha256sum "$D/template.xml" | cut -d' ' -f1)" = 90e9df2e518b6b71b85f7086128a28b7c37c538d1dfcdcc159fa8adcec530277 ] || fail TEMPLATE_HASH_MISMATCH
    sed -e "s|<port_dir>[^<]*</port_dir>|<port_dir>$PORT</port_dir>|" -e "s|<sound_card>[^<]*</sound_card>|<sound_card>$CARD</sound_card>|" "$D/template.xml" > "$D/config.next"
    pid=$(pidof "$AD")
    if [ -n "$pid" ] && [ -f "$D/runtime/used-$pid" ] && [ -f "$D/active" ] && hook_alive && cmp -s "$D/config.next" "$D/config.xml" && hardware_ready; then
        ensure_ui optional || echo UI_RETRY_PENDING
        echo READY_ALREADY_ACTIVE; exit 0
    fi
    mv "$D/config.next" "$D/config.xml"; chmod 644 "$D/config.xml"
    stop_injector
    rm -f "$D/active" "$D/runtime/ready-"* "$D/runtime/used-"* "$D/runtime/reloaded-"* "$D/runtime/error-"*
    if [ -z "$pid" ]; then
        am startservice --user 0 -n "$ADS"
        for n in 1 2 3 4 5; do pid=$(pidof "$AD"); [ -n "$pid" ] && break; sleep 1; done
    fi
    [ -n "$pid" ] || fail ADAYO_NOT_RUNNING
    [ "$(audio_threads)" -le 1 ] || fail DIRTY_PROCESS_MULTIPLE_AUDIO_THREADS
    [ "$(sha256sum "$D/frida-inject" | cut -d' ' -f1)" = 0d99be0e44d4ca3449056fa0a0b868fca1cf66c8ad704508949945afc07706aa ] || fail INJECTOR_HASH_MISMATCH
    nohup setsid "$D/frida-inject" -p "$pid" -s "$D/adapter.js" > "$D/injector.log" 2>&1 < /dev/null &
    for n in 1 2 3 4 5 6 7 8 9 10; do [ -f "$D/runtime/ready-$pid" ] && break; sleep 1; done
    [ -f "$D/runtime/ready-$pid" ] || { stop_injector; fail ADAPTER_NOT_READY; }
    hook_alive || { stop_injector; fail INJECTOR_IDENTITY_FAILED; }
    for n in 1 2 3 4 5 6 7 8 9 10; do [ -f "$D/runtime/reloaded-$pid" ] && break; sleep 1; done
    [ -f "$D/runtime/used-$pid" ] && [ -f "$D/runtime/reloaded-$pid" ] || { stop_injector; fail CONFIG_NOT_USED; }
    for n in 1 2 3 4 5 6 7 8; do hardware_ready && break; sleep 1; done
    hardware_ready || { stop_injector; fail HARDWARE_NOT_OPEN_BY_FM_PROCESS; }
    am startservice --user 0 -n "$RDS"
    ensure_ui optional || echo UI_RETRY_PENDING
    echo "$pid $PORT $CARD" > "$D/active"
    echo "READY serial=$PORT audio_card=$CARD pid=$pid"
    ;;
stop)
    stop_injector
    rm -f "$D/active" "$D/runtime/ready-"* "$D/runtime/used-"* "$D/runtime/reloaded-"* "$D/runtime/error-"*
    echo STOPPED
    ;;
install-components)
    # Android PackageManager enforces original sharedUID signatures.
    [ "$(getprop ro.build.version.sdk)" = 30 ] || fail UNTESTED_ANDROID_VERSION
    [ "$(getenforce)" = Permissive ] || fail SELINUX_POLICY_REQUIRED
    for entry in "$AD:AdayoDAB.apk" "$RD:RdsApp.apk"; do
        pkg=${entry%%:*}; file=${entry#*:}
        if [ -z "$(pm path "$pkg")" ]; then
            pm install "$D/$file" || fail "INSTALL_FAILED $pkg"
        else echo "PRESENT $pkg"; fi
    done
    ;;
log-start)
    # Preserve the prior boot's evidence before a new FM session changes state.
    boot_id=$(cat /proc/sys/kernel/random/boot_id)
    if [ "$boot_id" != "$(cat "$D/session-boot-id" 2>/dev/null)" ]; then
        [ ! -f "$D/session-start.txt" ] || cp "$D/session-start.txt" "$D/session-previous.txt"
        {
            date; echo "BOOT_ID=$boot_id"; cat /proc/uptime
            getprop ro.boot.bootreason; getprop sys.boot.reason; getprop persist.sys.boot.reason
            echo '=== SAVED FM BEFORE ADAPTER START ==='
            cat /data/user/0/com.adayo.service.dab/shared_prefs/save_db.xml 2>/dev/null
        } > "$D/session-start.txt"
        echo "$boot_id" > "$D/session-boot-id"
    fi
    for p in $(pidof logcat); do
        cmd=$(tr '\000' ' ' < /proc/$p/cmdline 2>/dev/null)
        case "$cmd" in *" -f $D/capture.log "*)
            case "$cmd" in *" RdsDataModel:V PlayView:V "*) echo LOG_ALREADY_RECORDING; exit 0;;
            *) echo LOG_PROFILE_UPGRADE; stop_log; sleep 1; break;; esac
        ;; esac
    done
    for f in "$D/capture.log" "$D/capture.log.1" "$D/capture.log.2"; do [ ! -f "$f" ] || chmod 600 "$f"; done
    nohup setsid logcat -b main -b system -b crash -v threadtime -T 1 -r 1024 -n 2 -f "$D/capture.log" 'DABService:V' 'DabAudioManager:V' 'PcmPlayThread:W' 'AudioTrack:W' 'RdsManager:V' 'PateoDabManager:V' 'DABManager:V' 'DABManagerImpl:V' 'RdsDataModel:V' 'PlayView:V' 'RadioListView:V' 'PlayViewAdapter:V' 'FmView:V' 'RdsPlayer:V' 'AudioPolicyManager:V' 'AndroidRuntime:E' 'DEBUG:E' '*:S' > "$D/logcat-launch.log" 2>&1 < /dev/null &
    sleep 1
    found=0
    for p in $(pidof logcat); do
        cmd=$(tr '\000' ' ' < /proc/$p/cmdline 2>/dev/null)
        case "$cmd" in *" -f $D/capture.log "*) found=1;; esac
    done
    [ "$found" = 1 ] || fail LOG_START_FAILED
    date > "$D/recording"
    echo LOG_RECORDING_STARTED
    ;;
log-stop)
    stop_log
    echo LOG_RECORDING_STOPPED
    ;;
diagnostic)
    echo '=== FM BETA 0.5.1 / DEVICE ==='
    date; id; getprop ro.build.fingerprint; getprop ro.build.display.id
    getprop ro.product.model; getprop ro.build.version.sdk; uname -a; getenforce
    echo '=== BOOT / SAVED FREQUENCY ==='
    cat /proc/sys/kernel/random/boot_id /proc/uptime
    getprop ro.boot.bootreason; getprop sys.boot.reason; getprop persist.sys.boot.reason
    getprop ro.vendor.build.fingerprint; getprop ro.bootimage.build.fingerprint
    cat "$D/session-previous.txt" "$D/session-start.txt" 2>/dev/null
    echo '=== CURRENT FM PREFERENCES ==='
    cat /data/user/0/com.adayo.service.dab/shared_prefs/save_db.xml 2>/dev/null
    cat /data/user/0/ru.local.voyah.fmloader/shared_prefs/fm.xml 2>/dev/null
    scan_snapshot
    echo '=== APP EXIT HISTORY ==='
    for pkg in "$AD" "$RD" ru.local.voyah.fmloader; do
        timeout 4 dumpsys activity exit-info "$pkg" 2>/dev/null | head -100
    done
    crash_snapshot
    echo '=== USB / DRIVERS ==='
    cat /proc/asound/cards
    ls -l /sys/bus/usb/drivers/cdc_acm /sys/bus/usb/drivers/snd-usb-audio
    ls -lZ /dev/ttyACM* /dev/snd/pcmC*D0c
    for card in /proc/asound/card[0-9]*; do
        echo "$card"; cat "$card/usbid" "$card/id" "$card/stream0" 2>/dev/null
    done
    echo '=== COMPATIBILITY CHECK ==='
    (checks; echo "CHECK_OK serial=$PORT audio_card=$CARD")
    echo '=== PACKAGES ==='
    for pkg in "$AD" "$RD"; do
        path=$(pm path "$pkg" | head -1 | sed 's/^package://'); echo "$pkg: $path"
        [ -n "$path" ] && sha256sum "$path"
        dumpsys package "$pkg" | grep -E 'versionCode=|versionName=|sharedUser|userId=|primaryCpuAbi=|signatures='
    done
    echo '=== SERVICES / MEDIA ==='
    echo '=== BOOT ROOT CHANNEL ==='
    getprop init.svc.logcat_sdcard
    sha256sum /system/etc/init.logcat.sh /data/local/tmp/load.bin 2>/dev/null
    grep -n -E 'telnetd|load.bin|ensure_telnetd' /system/etc/init.logcat.sh /data/local/tmp/load.bin 2>/dev/null
    grep ':0017 ' /proc/net/tcp /proc/net/tcp6 2>/dev/null
    service check adayo.dab; service check qg.audio_policy
    dumpsys media_session
    dumpsys media.audio_flinger | grep -B 2 -A 2 'com.adayo.service.dab'
    echo '=== FM PROCESS ==='
    pid=$(pidof "$AD"); echo "ADAYO_PID=$pid"
    if [ -n "$pid" ]; then
        echo "PCM_THREADS=$(audio_threads)"
        ls -l /proc/$pid/fd
        for t in /proc/$pid/task/*/comm; do cat "$t"; done
    fi
    echo '=== ADAPTER ==='
    cat "$D/active" "$D/injector.log" "$D/broker.log" "$D/logcat-launch.log" "$D/runtime/ready-$pid" "$D/runtime/used-$pid" "$D/runtime/reloaded-$pid" "$D/runtime/error-$pid" 2>/dev/null
    echo '=== RECENT FM / CRASH LOGS ==='
    logcat -d -v threadtime -t 2400 | grep -i -E 'adayo|dabservice|dabaudio|pcmplay|rdsmanager|pateodab|rdsdatamodel|playview|radiolistview|fmview|rdsplayer|audiofocus|audiopolicy|fullscan|scanstatus|scanstate|linker|fatal exception|avc: denied' | tail -900
    echo '=== RECORDED LOGS ==='
    for f in "$D/capture.log.2" "$D/capture.log.1" "$D/capture.log"; do
        [ -f "$f" ] && { echo "FILE $f"; tail -c 1048576 "$f"; }
    done
    exit 0
    ;;
*) fail 'USAGE check|status|start|stop|install-components|diagnostic|log-start|log-stop';;
esac
