'use strict';
var DIR = '/data/local/tmp/voyah-fm-loader-v1';
var CONFIG = DIR + '/config.xml';
function marker(name, text) {
    var f = new File(DIR + '/runtime/' + name + '-' + Process.id, 'w');
    f.write(text + '\n'); f.close();
}
Java.perform(function () {
    marker('ready', 'READY ' + Process.id);
    // Apply two verified config fields in place. No service recreation, I/O hook,
    // PCM reader, audio writes or lifecycle calls from the adapter.
    var attempts = 0;
    function scan() {
    var matches = [];
    attempts++;
    Java.choose('com.adayo.dab.DABService', {
        onMatch: function (instance) { matches.push(Java.retain(instance)); },
        onComplete: function () {
            if (matches.length === 0 && attempts < 10) {
                setTimeout(function () { Java.perform(scan); }, 500);
                return;
            }
            if (matches.length !== 1) {
                marker('error', 'SERVICE_INSTANCE_COUNT ' + matches.length);
                matches.forEach(function (x) { x.$dispose(); });
                return;
            }
            Java.scheduleOnMainThread(function () {
                try {
                    var stream = Java.use('java.io.FileInputStream').$new(CONFIG);
                    var parser = Java.use('android.util.Xml').newPullParser();
                    var card = -1, port = '';
                    try {
                        parser.setInput(stream, 'UTF-8');
                        var event = parser.getEventType();
                        while (event !== 1) {
                            if (event === 2) {
                                var name = String(parser.getName());
                                if (name === 'sound_card') card = Number(String(parser.nextText()).trim());
                                if (name === 'port_dir') port = String(parser.nextText()).trim();
                            }
                            event = parser.next();
                        }
                    } finally { stream.close(); }
                    if (!Number.isInteger(card) || card < 0 || card > 255 || !/^\/dev\/ttyACM[0-9]+$/.test(port)) throw new Error('INVALID_CONFIG');
                    var service = matches[0];
                    var field = service.getClass().getDeclaredField('W'); field.setAccessible(true);
                    var config = field.get(service);
                    var klass = config.getClass();
                    var pcm = klass.getDeclaredField('f'); pcm.setAccessible(true);
                    var uart = klass.getDeclaredField('a'); uart.setAccessible(true);
                    var before = pcm.getInt(config);
                    pcm.setInt(config, card);
                    uart.set(config, Java.use('java.lang.String').$new(port));
                    marker('used', 'CONFIG_READ ' + CONFIG);
                    marker('reloaded', 'CONFIG_APPLIED_IN_PLACE old_card=' + before + ' card=' + card + ' port=' + port);
                } catch (e) { marker('error', String(e)); }
                finally { matches[0].$dispose(); }
            });
        }
    });
    }
    scan();
});
