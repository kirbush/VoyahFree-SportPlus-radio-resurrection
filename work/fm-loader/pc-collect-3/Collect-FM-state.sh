#!/system/bin/sh
# Read existing state only. This script is passed over ADB, never installed.
D=/data/local/tmp/voyah-fm-loader-v1
echo VOYAH_PC_DIAGNOSTIC_BEGIN
dump() {
    title=$1; seconds=$2; shift 2
    echo "=== $title ==="
    { timeout "$seconds" "$@"; echo "COMMAND_EXIT=$?"; } 2>&1 | head -c 262144
    echo
}
filter_crashes() {
    program='
        BEGIN{matched=0}
        /^=/{keep=0}
        /^[0-9][0-9][0-9][0-9]-/{header=$0}
        /^DROPBOX_COMMAND_EXIT=/{print;keep=0;next}
        /^Process:/{
            keep=($0 ~ /^Process:[[:space:]]*(com\.pateo\.rdsapp|com\.adayo\.service\.dab|ru\.local\.voyah\.fmloader|ru\.local\.voyah\.fmdiagnostics|com\.qinggan\.app\.radio)([[:space:],:]|$)/)
            if(keep) matched++
            if(keep && header != "") print header
        }
        keep{print}
        END{if(matched==0) print "NO_MATCHING_FM_CRASH_ENTRY"}
    '
    if command -v awk >/dev/null 2>&1; then awk "$program"
    elif command -v busybox >/dev/null 2>&1; then busybox awk "$program"
    else cat >/dev/null; echo CRASH_FILTER_UNAVAILABLE; fi
}
echo '=== DEVICE ==='
date; id; cat /proc/sys/kernel/random/boot_id /proc/uptime
for prop in ro.build.fingerprint ro.build.display.id ro.build.version.incremental ro.build.description ro.build.version.sdk ro.boot.bootreason sys.boot.reason; do
    echo "$prop=$(getprop "$prop")"
done
getenforce
echo '=== EXISTING POWER / FM PROTOCOL LOGS ==='
# Capture scarce rings before the slower FM/helper snapshots. Tag "b" is obfuscated.
{ timeout 7 logcat -b main -b system -b events -d -v threadtime; echo "POWER_PROTOCOL_LOG_COMMAND_EXIT=$?"; } 2>&1 | grep -i -E 'StateManager|VoyahPolicy|BootControlModel|bootcontrol|qg_boot_control_BootAnimation|BootAnimation|CarPowerManagementService|PowerManagerService|SurfaceFlinger.*(power|boot|display|suspend)|boot_progress|power_sleep|power_screen|cmd_ind_radio_info|newFMFreq|newAMFreq|handleRadioInfoUpdate|DAB.*(uart|config.*ack)|POWER_PROTOCOL_LOG_COMMAND_EXIT' | tail -c 524288
echo
dump 'UI BEFORE / ACTIVITY STACK' 5 dumpsys activity activities
dump 'WINDOWS BEFORE' 5 dumpsys window windows
echo '=== CORE EVENTS ==='
for file in /data/user/0/ru.local.voyah.fmloader/files/events.previous.log /data/user/0/ru.local.voyah.fmloader/files/events.log; do
    echo "FILE $file"; tail -c 1048576 "$file" 2>&1
done
echo '=== FM HELPER ==='
if [ "$(id -u)" = 0 ] && [ -f "$D/helper.sh" ]; then
    for attempt in 1 2 3; do
        echo "HELPER_ATTEMPT=$attempt"
        timeout 85 sh "$D/helper.sh" diagnostic
        result=$?; echo "HELPER_EXIT=$result"
        [ "$result" = 1 ] || break
        sleep 1
    done
else echo HELPER_UNAVAILABLE_OR_DENIED; fi
echo '=== CORE / DIAGNOSTIC EXIT HISTORY ==='
for package in ru.local.voyah.fmloader ru.local.voyah.fmdiagnostics com.pateo.rdsapp; do
    dump "EXIT $package" 4 dumpsys activity exit-info "$package"
done
dump 'CRASH TEXT / BUFFER' 5 logcat -b crash -d -v threadtime -t 800
echo '=== TARGETED DROPBOX CRASHES ==='
for tag in system_app_crash data_app_crash; do
    echo "DROPBOX_TAG=$tag"
    { timeout 6 dumpsys dropbox --print "$tag"; echo "DROPBOX_COMMAND_EXIT=$?"; } 2>&1 | filter_crashes | tail -c 262144
    echo
done
echo '=== LOGGING CONFIGURATION ==='
getprop | grep -E 'log\.tag|persist\.log|logd|logcat|ro\.debuggable|ro\.build\.type'
dump 'LOG BUFFER SIZES' 4 logcat -g
ls -l "$D"/capture.log* "$D/logcat-launch.log" 2>&1
echo '=== RELATED PROCESSES ==='
ps -A -o USER,PID,ARGS 2>&1 | grep -E 'fmloader|fmdiagnostics|pateo.rdsapp|adayo|qinggan.app.radio|logcat|broker.sh|frida-inject' | head -150
echo '=== INSTALLED APP VERSIONS ==='
for package in ru.local.voyah.fmloader ru.local.voyah.fmdiagnostics com.pateo.rdsapp; do
    echo "PACKAGE=$package"
    timeout 4 dumpsys package "$package" 2>&1 | grep -E 'versionCode=|versionName=|userId=|firstInstallTime=|lastUpdateTime='
done
dump 'UI AFTER / ACTIVITY STACK' 5 dumpsys activity activities
dump 'WINDOWS AFTER' 5 dumpsys window windows
echo '=== OEM POWER / LOGO (PASSIVE SNAPSHOT) ==='
# These OEM dump services accept simulation/control arguments. Never pass any.
dump 'QG POWER MANAGER' 5 dumpsys qg.power_manager
dump 'OEM BOOTCONTROL' 5 dumpsys bootcontrol
dump 'ANDROID POWER' 4 dumpsys power
echo '=== CAR POWER HISTORY ==='
{ timeout 5 dumpsys car_service; echo "CAR_POWER_COMMAND_EXIT=$?"; } 2>&1 | grep -i -A 40 -B 5 -E 'power|suspend|resume|shutdown|CAR_POWER_COMMAND_EXIT' | head -c 262144
echo
dump 'COMPOSITOR LAYERS' 4 dumpsys SurfaceFlinger --list
echo '=== POWER COMPONENT IDENTITIES ==='
for process in system_server surfaceflinger bootcontrol com.qinggan.powermanager com.qinggan.systemui com.qinggan.app.launcher; do
    echo "PROCESS=$process"
    for pid in $(pidof "$process" 2>/dev/null); do
        case "$pid" in ''|*[!0-9]*) continue;; esac
        echo "PID=$pid"
        timeout 2 cat "/proc/$pid/stat" "/proc/$pid/comm" 2>&1
    done
done
echo '=== EXACT FIRMWARE POWER FILES ==='
path=$(pm path com.qinggan.powermanager 2>/dev/null | head -1 | sed 's/^package://')
if [ -n "$path" ]; then timeout 3 sha256sum "$path" 2>&1; else echo POWER_MANAGER_APK_UNAVAILABLE; fi
timeout 3 sha256sum /system/bin/bootcontrol /system/bin/bootanimation /system/media/bootanimation.zip 2>&1
for file in /system/etc/qinggan/power_manager.xml /system/etc/qinggan/str_feature.xml; do
    echo "FILE=$file"; timeout 2 cat "$file" 2>&1
done
echo '=== BOOT / ANIMATION PROPERTIES ==='
getprop | grep -E 'init\.svc\.(bootanim|bootcontrol)|sys\.bootanim|service\.bootanim|sys\.boot_completed|ro\.boottime\.(zygote|surfaceflinger|bootcontrol|bootanim)|sys\.power|ro\.boot\.bootreason|sys\.boot\.reason'
echo '=== KERNEL SUSPEND / RESUME ==='
{ timeout 4 dmesg; echo "KERNEL_COMMAND_EXIT=$?"; } 2>&1 | grep -i -E 'suspend|resume|wakeup|freezing|PM:|KERNEL_COMMAND_EXIT' | tail -c 131072
echo
for file in /sys/power/suspend_stats/success /sys/power/suspend_stats/fail /sys/power/suspend_stats/last_failed_step /sys/kernel/debug/wakeup_sources; do
    echo "FILE=$file"; { timeout 2 cat "$file"; echo "COMMAND_EXIT=$?"; } 2>&1 | head -c 65536
done
echo VOYAH_PC_DIAGNOSTIC_END
exit 0
