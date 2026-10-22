const fs=require('fs'), vm=require('vm'), assert=require('assert');
const source=fs.readFileSync(__dirname+'/assets/adapter.js','utf8');
function trial(card,port,count=1){
 let scheduled, closed=0, files={}, disposed=0, scans=0, timers=[];
 const cfg={card:2,port:'/dev/ttyACM0'};
 cfg.getClass=()=>({getDeclaredField:name=>({setAccessible:()=>{},getInt:o=>o.card,setInt:(o,v)=>{assert.equal(name,'f');o.card=v;},set:(o,v)=>{assert.equal(name,'a');o.port=v;}})});
 const service={getClass:()=>({getDeclaredField:name=>{assert.equal(name,'W');return {setAccessible:()=>{},get:()=>cfg};}}),$dispose:()=>disposed++};
 let i=-1, entries=[['sound_card',String(card)],['port_dir',port]];
 const parser={setInput:()=>{},getEventType:()=>0,next:()=>++i<entries.length?2:1,getName:()=>entries[i][0],nextText:()=>entries[i][1]};
 const ctx={Process:{id:123},console,setTimeout:f=>timers.push(f),File:function(path){this.write=s=>files[path]=s;this.close=()=>{};},Java:{
  perform:f=>f(), retain:x=>x, scheduleOnMainThread:f=>scheduled=f,
  choose:(name,cb)=>{assert.equal(name,'com.adayo.dab.DABService');const found=Array.isArray(count)?count[Math.min(scans,count.length-1)]:count;scans++;for(let n=0;n<found;n++)cb.onMatch(service);cb.onComplete();},
  use:name=>{if(name==='java.io.FileInputStream')return {$new:path=>{assert.equal(path,ctx.CONFIG);return{close:()=>closed++};}};
   if(name==='android.util.Xml')return{newPullParser:()=>parser};if(name==='java.lang.String')return{$new:s=>s};throw Error('Unexpected Java API: '+name);}
 }};
 vm.runInNewContext(source,ctx);while(timers.length){assert(scans<20,'retry must be bounded');timers.shift()();}if(scheduled)scheduled();return{cfg,files,closed,disposed,ctx,scans};
}
let r=trial(3,'/dev/ttyACM4');assert.equal(r.cfg.card,3);assert.equal(r.cfg.port,'/dev/ttyACM4');assert.equal(r.closed,1);assert.equal(r.disposed,1);
assert(r.files[r.ctx.DIR+'/runtime/reloaded-123']);assert(r.files[r.ctx.DIR+'/runtime/used-123']);
console.log('PASS data XML applies dynamic card/port to existing config; stream/retained object released');
for(const args of [[-1,'/dev/ttyACM0'],[1,'/dev/other'],[1.5,'/dev/ttyACM0']]){r=trial(...args);assert.equal(r.cfg.card,2);assert(r.files[r.ctx.DIR+'/runtime/error-123']);}
console.log('PASS malformed card/port rejected before mutating config');
for(const n of [0,2]){r=trial(1,'/dev/ttyACM0',n);assert.equal(r.cfg.card,2);assert(r.files[r.ctx.DIR+'/runtime/error-123']);}
console.log('PASS absent/duplicate service rejected; no lifecycle or I/O interception APIs used');
r=trial(1,'/dev/ttyACM0',[0,0,1]);assert.equal(r.scans,3);assert.equal(r.cfg.card,1);assert(r.files[r.ctx.DIR+'/runtime/reloaded-123']);
console.log('PASS cold-start service becomes available without lifecycle restart');
