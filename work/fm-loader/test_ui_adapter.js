const assert=require('assert');const fs=require('fs');const path=require('path');
const source=path.join(__dirname,'assets/ui.js');
assert(fs.existsSync(source),'OEM menu/observer adapter is missing');
const {registerDisplayObserver}=require(source);
let registrations=0;
function observer(name){return {getClass:()=>({getName:()=>name})};}
const display=observer('com.qinggan.media.helper.utils.DisplayUtils$1');
const other=observer('com.example.OtherObserver');
const list=[];const target={mObservers:{value:{contains:o=>list.includes(o)}}};
const original={call:(self,o)=>{if(list.includes(o))throw new Error('already registered');list.push(o);registrations++;}};
registerDisplayObserver(original,target,display);
registerDisplayObserver(original,target,display);
assert.equal(registrations,1,'same display observer must be registered only once');
const second=observer('com.qinggan.media.helper.utils.DisplayUtils$1');
registerDisplayObserver(original,target,second);assert.equal(registrations,2,'different observer instances are preserved');
registerDisplayObserver(original,target,other);
assert.throws(()=>registerDisplayObserver(original,target,other),/already registered/,'unrelated failures must not be hidden');
assert.throws(()=>registerDisplayObserver({call:()=>{throw new Error('different failure')}},target,observer('com.qinggan.media.helper.utils.DisplayUtils$1')),/different failure/);
let fallback=false;
registerDisplayObserver({call:()=>{fallback=true;}},{},observer('com.qinggan.media.helper.utils.DisplayUtils$1'));
assert(fallback,'Unknown observer implementation must use OEM behavior');
console.log('PASS RDS exact-observer idempotency, distinct instances and unrelated exceptions');
const vm=require('vm');const callbacks=[];let inMain=false,installed=false,marker='';
const classes={
 'android.app.ActivityThread':{currentPackageName:()=> 'com.pateo.rdsapp',currentApplication:()=>({valid:inMain})},
 'android.database.Observable':{registerObserver:{overload:()=>({call:()=>{}})}},
 'ru.local.voyah.fmloader.ui.MenuBridge':{install:app=>{assert(app.valid,'JNI instance captured outside its main-thread callback');installed=true;}},
 'android.app.Application':{}
};
const sandbox={Process:{id:111},console:{log:()=>{}},File:function(name){assert(name.endsWith('/ui-ready-111'));this.write=s=>{marker=s};this.flush=()=>{};this.close=()=>{};},
 Java:{perform:f=>f(),use:name=>{assert(classes[name],name);return classes[name]},cast:o=>o,openClassFile:()=>({load:()=>{}}),scheduleOnMainThread:f=>callbacks.push(f),choose:()=>{throw new Error('Unsafe ART heap scan');}}};
vm.runInNewContext(fs.readFileSync(source,'utf8'),sandbox);
assert(!installed,'Menu must be installed on the main thread');
inMain=true;callbacks.shift()();
assert(installed&&marker.startsWith('0.5.1'),'Native lifecycle menu not ready');
console.log('PASS UI startup uses native lifecycle callbacks and current JNI references, without ART heap scan');
