#!/system/bin/sh
# ADB-started root broker. Only fixed FM operations; no caller-supplied shell.
umask 077
D=/data/local/tmp/voyah-fm-loader-v1
B=$D/mailbox
exec 0>"$D/broker.lock"
flock -n 0 || exit 0
echo $$ > "$D/broker.pid"
cat /proc/sys/kernel/random/boot_id > "$D/online.new"
chmod 644 "$D/online.new"
mv -f "$D/online.new" "$B/online"
trap 'rm -f "$B/online"; exit' TERM INT EXIT
n=0
while :; do
    if [ -f "$B/request" ]; then
        read -r token action extra < "$B/request"
        rm -f "$B/request"
        case "$token" in ''|*[!a-zA-Z0-9-]*) continue;; esac
        [ "${#token}" -le 64 ] || continue
        case "$action:$extra" in check:|status:|start:|stop:|install-components:|diagnostic:|log-start:|log-stop:|ui-start:)
            sh "$D/helper.sh" "$action" > "$D/reply.body" 2>&1
            code=$?
            if [ "$code" = 0 ]; then echo OK > "$D/reply.new"; else echo ERROR > "$D/reply.new"; fi
            cat "$D/reply.body" >> "$D/reply.new"
            chmod 644 "$D/reply.new"
            mv -f "$D/reply.new" "$B/$token.reply"
            ;;
        esac
    fi
    n=$((n+1))
    if [ "$n" -ge 30 ]; then
        n=0
        if [ -z "$(pm path ru.local.voyah.fmloader)" ]; then
            sh "$D/helper.sh" log-stop > "$D/uninstall-log-stop.txt" 2>&1
            sh "$D/helper.sh" stop > "$D/uninstall.log" 2>&1
            exit 0
        fi
    fi
    sleep 0.3
done
