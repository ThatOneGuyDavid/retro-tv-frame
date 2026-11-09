// Exercise the real viewer's layer-tree logic with a minimal DOM, not a WebGL test.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const file=process.argv[2]||path.join(__dirname,'../design/assembly/assembly-viewer.html');
const html=fs.readFileSync(file,'utf8');
const names=JSON.parse(html.split('const raw=')[1].split(';const c=')[0]).map(p=>p.name);
const start=html.indexOf('const leafLabel='),end=html.indexOf('\nfunction draw()',start);
if(start<0||end<0)throw Error('Layer tree not found');
class Element{constructor(){this.children=[];this.checked=false;this.indeterminate=false}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
const scope={parts:names.map(name=>({name,visible:true})),document:{createElement:()=>new Element(),createTextNode:t=>t,getElementById:()=>new Element()},draw:()=>{}};
const tests=`
function assert(value,message){if(!value)throw Error(message)}
assert(descendants(layerRoot).length===parts.length,'All parts represented');
assert(new Set(descendants(layerRoot)).size===parts.length,'Parts represented only once');
const upper=layerNodes.get('upper-knob'),controls=layerNodes.get('controls');
assert(descendants(upper).length===5,'Five upper knob parts');
setLayerVisibility(upper,false);
assert(descendants(upper).every(p=>!p.visible),'Upper knob hidden');
assert(layerNodes.get('lower-knob').checkbox.checked,'Lower knob unaffected');
assert(controls.checkbox.indeterminate&&layerRoot.checkbox.indeterminate,'Ancestors show mixed state');
setLayerVisibility(controls,false);
assert(descendants(controls).every(p=>!p.visible),'Entire control section hidden');
assert(!controls.checkbox.indeterminate&&!controls.checkbox.checked,'Hidden group state');
assert(layerNodes.get('frame').checkbox.checked,'Frame unaffected');
setLayerVisibility(controls,true);
assert(upper.checkbox.checked&&layerRoot.checkbox.checked,'Re-enabling group restores all descendants');
const first=layerNodes.get(descendants(upper)[0].name);setLayerVisibility(first,false);
assert(upper.checkbox.indeterminate&&controls.checkbox.indeterminate,'Leaf toggle updates ancestors');
setLayerVisibility(layerRoot,false);assert(parts.every(p=>!p.visible),'All off');
setLayerVisibility(layerRoot,true);assert(parts.every(p=>p.visible),'All on');
`;
vm.runInNewContext(html.slice(start,end)+tests,scope);
console.log('PASS: actual viewer tree, unique membership, whole-knob/section/root toggles, mixed states, sibling isolation.');
const zoomStart=html.indexOf('function baseZoom()'),zoomEnd=html.indexOf("window.addEventListener('resize'",zoomStart);
if(zoomStart>=0){
 const controls=new Map();
 const zoomScope={document:{getElementById:id=>{if(!controls.has(id))controls.set(id,new Element());return controls.get(id)}}};
 const wheel=html.match(/c\.onwheel=e=>\{.*?\};/s)[0];
 const zoomTests=`
 function assert(value,message){if(!value)throw Error(message)}
 fitView();assert(Math.abs(zoom/baseZoom()-1)<1e-9,'Fit equals 100 percent');
 document.getElementById('zoom').oninput({target:{value:'250'}});
 assert(Math.abs(zoom/baseZoom()-2.5)<1e-9,'Slider changes camera zoom');
 assert(document.getElementById('zoom-value').textContent==='250%','Slider readout');
 c.onwheel({preventDefault(){},deltaY:100000});assert(Math.abs(zoom/baseZoom()-.25)<1e-9,'Wheel lower limit');
 assert(document.getElementById('zoom-value').textContent==='25%','Wheel syncs readout');
 c.onwheel({preventDefault(){},deltaY:-100000});assert(Math.abs(zoom/baseZoom()-3)<1e-9,'Wheel upper limit');
 fitView();assert(document.getElementById('zoom-value').textContent==='100%','Fit resets slider');
 `;
 vm.runInNewContext('let zoom=1/500;const c={clientWidth:1200,clientHeight:900};function draw(){syncZoom()}\n'+html.slice(zoomStart,zoomEnd)+wheel+zoomTests,zoomScope);
 console.log('PASS: slider zoom, percent readout, mouse-wheel synchronization/limits, fit reset.');
}
