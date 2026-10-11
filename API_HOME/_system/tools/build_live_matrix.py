"""Build templates/statistics_matrix_live.html from the approved prototype (08_NEW_STATION_SPECS).

Keeps the approved design exactly (layout, styles, encodings, matrix, family map, wall) and replaces
only the parts that produced demo numbers:
  * the random data generator  -> a bridge that reads LIVE (statistics.json) into the same METRICS shape
  * the 12 headline tiles       -> the headline list from statistics.json
  * the 15 specialised charts   -> the same chart forms fed from statistics.json; a chart whose data
                                   does not exist yet says what it is waiting for instead of drawing
  * demo labels                 -> live labels
Re-run after the prototype changes:  python tools/build_live_matrix.py
"""
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
SRC = HOME.parent / "08_NEW_STATION_SPECS" / "STATISTICS_MATRIX_PROTOTYPE.html"
if not SRC.exists():
    SRC = HOME / "templates" / "statistics_matrix.html"
OUT = HOME / "templates" / "statistics_matrix_live.html"

DATA = r'''/* ---------- live data (statistics.json) ---------- */
var LIVE=__LIVE_PAYLOAD__;
function clamp(x,a,b){return Math.max(a,Math.min(b,x));}
function zOf(p){var q=clamp(p/100,.005,.995);var t=Math.sqrt(-2*Math.log(q<.5?q:1-q));var z=t-(2.515517+.802853*t+.010328*t*t)/(1+1.432788*t+.189269*t*t+.001308*t*t*t);return q<.5?-z:z;}
var SECT=["Whole paper"];
var FAM=[],famIx={};
(LIVE.families||[]).forEach(function(f){famIx[f.k]=FAM.length;FAM.push({k:f.k,n:f.n,src:f.src,sect:false,m:[]});});
function goodOf(p,dir){if(p==null)return null;if(dir==="hi")return p;if(dir==="lo")return 100-p;return clamp(100-Math.abs(p-50)*2,1,99);}
var METRICS=[];
(LIVE.metrics||[]).forEach(function(x){
  if(typeof x.value!=="number"||!isFinite(x.value))return;
  var fi=famIx[x.family];if(fi==null)return;
  var dir=x.dir||"band",gc=goodOf(x.corpus_percentile,dir),ga=goodOf(x.academic_percentile,dir);
  METRICS.push({fam:fi,name:x.name,sec:"Whole paper",dir:dir,unit:x.unit||"",dec:x.dec==null?2:x.dec,val:x.value,
    gc:gc==null?50:gc,gcKnown:gc!=null,ga:ga,pc:x.corpus_percentile==null?50:x.corpus_percentile,
    z:Math.abs(zOf(x.corpus_percentile==null?50:x.corpus_percentile)),src:/^api/.test(x.method||"")?"A":"L",
    low:!!x.runs_disagree,series:x.series_percentile,dv:x.change_since_previous,prev:x.previous,method:x.method||"",cn:x.corpus_n||0});
});
FAM=FAM.filter(function(f,fi){return METRICS.some(function(m){return m.fam===fi;});});
(function(){var map={};FAM.forEach(function(f,i){map[f.k]=i;});var old={};Object.keys(famIx).forEach(function(k){old[famIx[k]]=k;});
  METRICS.forEach(function(m){m.fam=map[old[m.fam]];});})();
var N=METRICS.length;
var X_=LIVE.extras||{};
'''

TILES = r'''function find(fk,name){for(var i=0;i<N;i++){var m=METRICS[i];if(FAM[m.fam].k===fk&&m.name===name)return m;}}
function renderTiles(){
  var known=METRICS.filter(function(m){return m.gcKnown;});
  var overall=known.length?Math.round(known.reduce(function(a,m){return a+m.gc;},0)/known.length):null;
  var picks=[{k:"Overall (all statistics vs corpus)",v:overall==null?"—":overall,u:overall==null?"":"/100",g:overall}];
  (LIVE.headline||[]).slice(0,11).forEach(function(h){picks.push({k:h.label,m:find(h.family,h.name)});});
  var host=document.getElementById("tiles");host.innerHTML="";
  picks.forEach(function(p){
    var g=p.m?(state.frame==="co"?(p.m.gcKnown?p.m.gc:null):p.m.ga):p.g;
    var val=p.m?fmt(p.m):(p.v==null?"—":p.v);
    var d=document.createElement("div");d.className="tile";
    d.innerHTML='<div class="k">'+p.k+'</div><div class="v num">'+(p.m||p.v!=null?val:"—")+(p.u?'<small>'+p.u+'</small>':(p.m&&p.m.unit?'<small>'+p.m.unit+'</small>':''))+'</div>'+
      '<div class="pbar"><i style="width:'+(g==null?0:g).toFixed(0)+'%;background:'+goodColor(g)+'"></i><u style="left:50%"></u></div>'+
      '<div class="p"><span>'+(state.frame==="co"?"vs corpus":"vs academic")+'</span><span>'+(g==null?(p.m||p.k.indexOf("Overall")===0?"no comparison yet":"not computed yet"):ord(g)+' pct')+'</span></div>';
    host.appendChild(d);
  });
}
'''

CHARTS = r'''/* ---------- specialised charts (live) ---------- */
var charts=document.getElementById("charts");
function card(title,what,build,needs){var d=document.createElement("div");d.className="chart";d.innerHTML='<h3>'+title+'</h3><div class="what">'+what+'</div>';
  var s=el("svg",{},null);var ok=false;try{ok=build(s,d)!==false;}catch(e){ok=false;}
  if(ok)d.appendChild(s);else{var w=document.createElement("div");w.className="what";w.style.fontStyle="italic";w.textContent="Not computed yet: needs "+needs+".";d.appendChild(w);}
  charts.appendChild(d);return d;}
var FR=["Love","Joy","Peace","Patience","Kindness","Goodness","Faithfulness","Gentleness","Self-control"];
var sv=X_.fruit_vectors||[],SENT=sv.length;
function hover(node,html){node.addEventListener("mousemove",function(e){showTip(e,html);});node.addEventListener("mouseleave",hideTip);}
function med(a){if(!a.length)return null;var s=a.slice().sort(function(x,y){return x-y;});return s[Math.floor(s.length/2)];}
function renderCharts(){
  charts.innerHTML="";
  var s1=css("--s1"),s2=css("--s2"),s3=css("--s3"),mu=css("--muted"),gr=css("--grid"),ax=css("--axis"),ink=css("--ink"),sur=css("--surface");
  function divColor(v){return v<=-2?css("--b3"):v===-1?css("--b1"):v===0?css("--mid"):v===1?css("--g1"):css("--g3");}
  var CM=LIVE.corpus_medians||{};

  card("Nine fruits, profile","Mean per-sentence score for each fruit. Solid: this paper. Dashed: corpus median (when the corpus has one).",function(s){
    var paper=FR.map(function(f){var m=find("fruit",f+", mean");return m?m.val:null;});if(paper.every(function(v){return v==null;}))return false;
    paper=paper.map(function(v){return v==null?0:v;});
    s.setAttribute("viewBox","0 0 340 290");var cx=170,cy=146,R=108;
    function pt(i,v){var a=-Math.PI/2+i*2*Math.PI/9, rr=R*(clamp(v,-.5,1.2)+.5)/1.7;return [cx+rr*Math.cos(a),cy+rr*Math.sin(a)];}
    [-.5,0,.6,1.2].forEach(function(v){var p=FR.map(function(_,i){return pt(i,v).join(",");}).join(" ");el("polygon",{points:p,fill:"none",stroke:v===0?ax:gr,"stroke-width":1},s);});
    FR.forEach(function(f,i){var e=pt(i,1.2);el("line",{x1:cx,y1:cy,x2:e[0],y2:e[1],stroke:gr},s);var l=pt(i,1.45);txt(s,l[0],l[1]+3,f,{"text-anchor":"middle","font-size":"10"});});
    var corp=FR.map(function(f){return CM[f+", mean"];});
    if(corp.every(function(v){return typeof v==="number";}))el("polygon",{points:corp.map(function(v,i){return pt(i,v).join(",");}).join(" "),fill:"none",stroke:mu,"stroke-width":1.5,"stroke-dasharray":"4 3"},s);
    el("polygon",{points:paper.map(function(v,i){return pt(i,v).join(",");}).join(" "),fill:s1,"fill-opacity":.14,stroke:s1,"stroke-width":2},s);
    paper.forEach(function(v,i){var p=pt(i,v);var c=el("circle",{cx:p[0],cy:p[1],r:4,fill:s1,stroke:sur,"stroke-width":2},s);hover(c,'<div class="t1">'+FR[i]+'</div><div class="num">'+v.toFixed(2)+' mean</div>');});
    txt(s,cx+3,cy-3,"0",{"class":"t-mono t-mut"});
  },"a 40_ANALYTICAL_ARMS run");

  card("Sentence by sentence, all nine fruits","Every sentence is a column. Blue moves toward the fruit, red moves away.",function(s){
    if(!SENT)return false;var W=340,cw=W/SENT,rh=13,H=9*rh+26;s.setAttribute("viewBox","0 0 "+(W+62)+" "+H);
    FR.forEach(function(f,j){txt(s,58,j*rh+10,f,{"text-anchor":"end","font-size":"9"});});
    for(var i=0;i<SENT;i++)for(var j=0;j<9;j++){el("rect",{x:62+i*cw,y:j*rh,width:cw+.05,height:rh-1.5,fill:divColor(sv[i][j])},s);}
    var hit=el("rect",{x:62,y:0,width:W,height:9*rh,fill:"transparent"},s);
    hit.addEventListener("mousemove",function(e){var b=hit.getBoundingClientRect();var i=clamp(Math.floor((e.clientX-b.left)/b.width*SENT),0,SENT-1);showTip(e,'<div class="t1">Sentence S'+String(i+1).padStart(3,"0")+'</div>'+FR.map(function(f,j){return '<div class="t2">'+f+' '+(sv[i][j]>0?"+":"")+sv[i][j]+'</div>';}).join(""));});
    hit.addEventListener("mouseleave",hideTip);
    [1,Math.round(SENT/2),SENT].forEach(function(n){txt(s,62+(n-1)*cw,9*rh+14,"S"+n,{"text-anchor":"middle","class":"t-mono t-mut","font-size":"9"});});
  },"per-sentence fruit scores from 40_ANALYTICAL_ARMS");

  card("Words vs meaning: counterfeit and hidden fruit","Each dot is a sentence. Across: how many love words it uses. Up: what it actually does for love.",function(s){
    var lw=X_.love_words||[];if(!SENT||!lw.length)return false;
    s.setAttribute("viewBox","0 0 340 250");var L=36,T=12,W=290,H=196;var mx=Math.max(6,Math.max.apply(null,lw));
    var X=function(v){return L+v/mx*W;},Y=function(v){return T+H-(v+2)/4*H;};
    el("rect",{x:X(1),y:Y(-1),width:W-(X(1)-L),height:H/4,fill:css("--b1"),"fill-opacity":.25},s);
    el("rect",{x:L,y:T,width:X(1)-L,height:H/4,fill:css("--g1"),"fill-opacity":.22},s);
    [-2,-1,0,1,2].forEach(function(v){el("line",{x1:L,x2:L+W,y1:Y(v),y2:Y(v),stroke:v===0?ax:gr},s);txt(s,L-6,Y(v)+3,(v>0?"+":"")+v,{"text-anchor":"end","class":"t-mono t-mut"});});
    txt(s,L+W/2,T+H+27,"love words in the sentence",{"text-anchor":"middle","font-size":"10"});
    for(var i=0;i<Math.min(SENT,lw.length);i++){var j=((i*37)%11-5)/5*3;var c=el("circle",{cx:X(lw[i])+j,cy:Y(sv[i][0]),r:3,fill:s1,"fill-opacity":.55,stroke:sur,"stroke-width":.8},s);
      (function(i){hover(c,'<div class="t1">S'+String(i+1).padStart(3,"0")+'</div><div class="t2">'+lw[i]+' love words · meaning '+(sv[i][0]>0?"+":"")+sv[i][0]+'</div>');})(i);}
    txt(s,L+W-4,Y(-1.85),"counterfeit",{"text-anchor":"end","class":"t-ink","font-weight":"600"});
    txt(s,X(0)+4,Y(1.75),"hidden fruit",{"class":"t-ink","font-weight":"600"});
  },"a 40_ANALYTICAL_ARMS run (sentence scores + lexicon hits)");

  card("Readability against the target band","Bar: this paper. Grey band: the target, when academic_norms.json sets one. Tick: corpus median.",function(s){
    var names=["Flesch–Kincaid grade","Gunning fog","SMOG","Coleman–Liau","ARI","Consensus grade"];var TB=LIVE.target_bands||{};
    var rows=names.map(function(n){return [n,find("read",n)];}).filter(function(r){return r[1];});if(!rows.length)return false;
    var W=210,L=112,rh=30;s.setAttribute("viewBox","0 0 340 "+(rows.length*rh+18));var X=function(v){return L+clamp((v-4)/18,0,1)*W;};
    rows.forEach(function(r,i){var m=r[1];var y=i*rh+4;txt(s,L-8,y+13,r[0],{"text-anchor":"end","font-size":"10"});
      el("rect",{x:L,y:y+4,width:W,height:14,fill:gr,rx:2},s);var band=TB[r[0]];
      if(band)el("rect",{x:X(band[0]),y:y+4,width:X(band[1])-X(band[0]),height:14,fill:ax,rx:2},s);
      var b=el("rect",{x:L,y:y+8,width:Math.max(2,X(m.val)-L),height:6,fill:s1,rx:3},s);
      if(typeof CM[r[0]]==="number")el("line",{x1:X(CM[r[0]]),x2:X(CM[r[0]]),y1:y+1,y2:y+21,stroke:ink,"stroke-width":2},s);
      txt(s,X(m.val)+4,y+16,m.val.toFixed(1),{"class":"t-mono t-ink","font-size":"10"});
      hover(b,'<div class="t1">'+r[0]+'</div><div class="num">'+m.val.toFixed(1)+'</div><div class="t2">'+(band?'target '+band[0]+'–'+band[1]:'no target band set')+'</div>');});
    [4,10,16,22].forEach(function(v){txt(s,X(v),rows.length*rh+14,v,{"text-anchor":"middle","class":"t-mono t-mut","font-size":"9"});});
  },"readability metrics (station 42)");

  card("Since the last version","Hollow: the previous run. Filled: this run. Each row is scaled to its own two values.",function(s){
    var rows=METRICS.filter(function(m){return typeof m.prev==="number"&&m.prev!==m.val;}).sort(function(a,b){return Math.abs((b.val-b.prev)/(Math.abs(b.prev)||1))-Math.abs((a.val-a.prev)/(Math.abs(a.prev)||1));}).slice(0,8);
    if(!rows.length)return false;var L=150,W=170,rh=24;s.setAttribute("viewBox","0 0 340 "+(rows.length*rh+20));
    rows.forEach(function(m,i){var lo=Math.min(m.prev,m.val),hi=Math.max(m.prev,m.val),pad=(hi-lo)*.25||1;var X=function(v){return L+(v-lo+pad)/(hi-lo+2*pad)*W;};var y=i*rh+12;
      txt(s,L-8,y+4,m.name,{"text-anchor":"end","font-size":"10"});el("line",{x1:L,x2:L+W,y1:y,y2:y,stroke:gr},s);
      el("line",{x1:X(m.prev),x2:X(m.val),y1:y,y2:y,stroke:s1,"stroke-width":2.5},s);
      el("circle",{cx:X(m.prev),cy:y,r:4.5,fill:sur,stroke:mu,"stroke-width":1.8},s);
      var c=el("circle",{cx:X(m.val),cy:y,r:5,fill:s1,stroke:sur,"stroke-width":2},s);hover(c,'<div class="t1">'+m.name+'</div><div class="t2">'+m.prev+' → '+fmt(m)+'</div>');});
  },"a previous 42_STATISTICS_WALL run of this item");

  card("What kind of claims","One square is one percent of all claims.",function(s){
    var names=["Descriptive claims","Causal claims","Theological claims","Empirical claims","Historical claims","Mathematical claims"],cols=[s1,s2,s3,css("--s4"),css("--s5"),css("--s7")];
    var cats=names.map(function(n,i){var m=find("claim",n);return m?[n.replace(" claims",""),m.val,cols[i]]:null;}).filter(Boolean);if(!cats.length)return false;
    var tot=cats.reduce(function(a,c){return a+c[1];},0);if(!tot)return false;cats.forEach(function(c){c[1]=Math.round(c[1]/tot*100);});
    s.setAttribute("viewBox","0 0 340 180");var k=0,sz=15,gap=2;
    cats.forEach(function(c){for(var n=0;n<c[1]&&k<100;n++,k++){var col=Math.floor(k/10),row=k%10;var r=el("rect",{x:4+col*(sz+gap),y:4+row*(sz+gap),width:sz,height:sz,rx:2,fill:c[2]},s);hover(r,'<div class="t1">'+c[0]+'</div><div class="num">'+c[1]+'%</div>');}});
    cats.forEach(function(c,i){el("rect",{x:190,y:14+i*22,width:10,height:10,rx:2,fill:c[2]},s);txt(s,206,23+i*22,c[0]+"  "+c[1]+"%",{"class":"t-ink","font-size":"11"});});
  },"claim-type counts (claims family; not produced by any station yet)");

  card("Master equation, ten slots","Each segment is one factor of χ. Darker is a closer fit. Grey means the paper has nothing in that role.",function(s){
    var ms=X_.me_slots||{};var slots=["G","M","E","S_eff","T","K","R","Q","F","C"];if(!Object.keys(ms).length)return false;
    s.setAttribute("viewBox","0 0 340 250");var cx=120,cy=124,ro=96,ri=60;
    var fitNames=["absent","stretched","analogous","direct"],fitCol=[css("--mid"),css("--q2"),css("--q3"),css("--q4")];var filled=0;
    slots.forEach(function(sl,i){var f=Math.max(0,fitNames.indexOf(ms[sl]||"absent"));if(f>0)filled++;
      var a0=-Math.PI/2+i*2*Math.PI/10+.025,a1=a0+2*Math.PI/10-.05;function P(r,a){return (cx+r*Math.cos(a)).toFixed(2)+" "+(cy+r*Math.sin(a)).toFixed(2);}
      var p=el("path",{d:"M"+P(ro,a0)+" A"+ro+" "+ro+" 0 0 1 "+P(ro,a1)+" L"+P(ri,a1)+" A"+ri+" "+ri+" 0 0 0 "+P(ri,a0)+" Z",fill:fitCol[f]},s);
      var am=(a0+a1)/2;txt(s,cx+(ro+13)*Math.cos(am),cy+(ro+13)*Math.sin(am)+3,sl,{"text-anchor":"middle","class":"t-ink","font-size":"10"});
      hover(p,'<div class="t1">Slot '+sl+'</div><div class="t2">fit: '+fitNames[f]+'</div>');});
    txt(s,cx,cy+2,filled+"/10",{"text-anchor":"middle","class":"t-ink","font-size":"24","font-weight":"500"});
    txt(s,cx,cy+18,"slots filled",{"text-anchor":"middle","class":"t-mut","font-size":"10"});
    fitNames.slice().reverse().forEach(function(n,i){el("rect",{x:250,y:70+i*22,width:12,height:12,rx:2,fill:fitCol[3-i]},s);txt(s,268,80+i*22,n,{"font-size":"11"});});
  },"the master-equation arm of 40_ANALYTICAL_ARMS");

  card("Hedging and certainty vs your norm","Difference from your corpus median, per 1,000 words. Right of centre means more than usual.",function(s){
    var rows=["Hedges","Boosters","Attitude markers","Self-mentions","Engagement markers","Absolutes (always/never/proves)"].map(function(n){var m=find("stance",n);return m&&typeof CM[n]==="number"?[n,m.val-CM[n]]:null;}).filter(Boolean);
    if(!rows.length)return false;var span=Math.max(1,Math.max.apply(null,rows.map(function(r){return Math.abs(r[1]);})));
    var L=150,W=170,rh=26,mid=L+W/2;s.setAttribute("viewBox","0 0 340 "+(rows.length*rh+22));
    el("line",{x1:mid,x2:mid,y1:0,y2:rows.length*rh,stroke:ax,"stroke-width":1.2},s);
    rows.forEach(function(r,i){var d=r[1];var y=i*rh+13;var x=mid+d/span*(W/2);txt(s,L-8,y+4,r[0],{"text-anchor":"end","font-size":"10"});
      el("line",{x1:mid,x2:x,y1:y,y2:y,stroke:d>=0?s2:s1,"stroke-width":2},s);
      var c=el("circle",{cx:x,cy:y,r:5,fill:d>=0?s2:s1,stroke:sur,"stroke-width":2},s);hover(c,'<div class="t1">'+r[0]+'</div><div class="num">'+(d>=0?"+":"")+d.toFixed(1)+' per 1k vs your median</div>');});
    txt(s,mid,rows.length*rh+16,"your median",{"text-anchor":"middle","class":"t-mut","font-size":"9"});
  },"at least two papers in the corpus (for the median)");

  card("Word frequency, log–log","Rank against frequency for every distinct word. A straight line is Zipf's law; the slope is in the matrix.",function(s){
    var z=X_.zipf||[];if(z.length<5)return false;var maxR=z[z.length-1][0],maxF=z[0][1];
    s.setAttribute("viewBox","0 0 340 240");var L=40,T=10,W=286,H=190;var lr=Math.log10(maxR)||1,lf=Math.log10(maxF)||1;
    var X=function(r){return L+Math.log10(r)/lr*W;},Y=function(f){return T+H-Math.log10(f)/lf*H;};
    [1,10,100,1000].filter(function(v){return v<=maxR;}).forEach(function(v){el("line",{x1:X(v),x2:X(v),y1:T,y2:T+H,stroke:gr},s);txt(s,X(v),T+H+13,v,{"text-anchor":"middle","class":"t-mono t-mut"});});
    [1,10,100].filter(function(v){return v<=maxF;}).forEach(function(v){el("line",{x1:L,x2:L+W,y1:Y(v),y2:Y(v),stroke:gr},s);txt(s,L-6,Y(v)+3,v,{"text-anchor":"end","class":"t-mono t-mut"});});
    for(var i=0;i<z.length;i=i<30?i+1:Math.ceil(i*1.06)){el("circle",{cx:X(z[i][0]),cy:Y(z[i][1]),r:2.6,fill:s1,"fill-opacity":.6},s);}
    txt(s,L+W/2,T+H+28,"rank",{"text-anchor":"middle","font-size":"10"});
  },"station 42");

  card("Where the sources come from","Area is the share of all references.",function(s){
    var items=[["Peer-reviewed","Peer-reviewed share",s1],["Books","Book share",s2],["Web","Web share",css("--s4")],["Self","Self-citation share",css("--s5")]].map(function(x){var m=find("cite",x[1]);return m&&m.val>0?[x[0],m.val,x[2]]:null;}).filter(Boolean);
    if(!items.length)return false;var tot=items.reduce(function(a,b){return a+b[1];},0);items.forEach(function(i){i[1]/=tot;});items.sort(function(a,b){return b[1]-a[1];});
    s.setAttribute("viewBox","0 0 340 190");var x=0,y=0,W=340,H=190;
    items.forEach(function(it,k){var rest=items.slice(k).reduce(function(a,b){return a+b[1];},0);var vert=(W-x)>(H-y);var share=it[1]/rest;var w=vert?(W-x)*share:(W-x),h=vert?(H-y):(H-y)*share;
      var r=el("rect",{x:x+1,y:y+1,width:Math.max(0,w-2),height:Math.max(0,h-2),rx:3,fill:it[2]},s);
      if(w>52&&h>30){txt(s,x+8,y+18,it[0],{"font-size":"11","font-weight":"600",style:"fill:"+sur});txt(s,x+8,y+32,Math.round(it[1]*100)+"%",{"class":"t-mono","font-size":"11",style:"fill:"+sur});}
      hover(r,'<div class="t1">'+it[0]+'</div><div class="num">'+Math.round(it[1]*100)+'% of references</div>');if(vert)x+=w;else y+=h;});
  },"source-type classification of the reference list");

  card("Coherence, with its uncertainty","Dot: score. Whisker: the range across independent AI runs (shown when there is more than one run).",function(s){
    var cd=X_.coherence_dimensions||{};var keys=Object.keys(cd);var total=find("cohs","Coherence score");if(!keys.length&&!total)return false;
    var rows=keys.map(function(k){return [k.replace(/_/g," "),cd[k].filter(function(v){return typeof v==="number";})];});if(total)rows.push(["Coherence score",[total.val]]);
    var L=150,W=170,rh=28;s.setAttribute("viewBox","0 0 340 "+(rows.length*rh+22));var X=function(v){return L+clamp(v,0,10)/10*W;};
    rows.forEach(function(r,i){if(!r[1].length)return;var v=r[1].reduce(function(a,b){return a+b;},0)/r[1].length;var lo=Math.min.apply(null,r[1]),hi=Math.max.apply(null,r[1]);var y=i*rh+14;
      txt(s,L-8,y+4,r[0],{"text-anchor":"end","font-size":"10"});el("line",{x1:L,x2:L+W,y1:y,y2:y,stroke:gr},s);
      if(hi>lo)el("line",{x1:X(lo),x2:X(hi),y1:y,y2:y,stroke:mu,"stroke-width":2},s);
      var c=el("circle",{cx:X(v),cy:y,r:5,fill:s1,stroke:sur,"stroke-width":2},s);hover(c,'<div class="t1">'+r[0]+'</div><div class="num">'+v.toFixed(1)+(hi>lo?' (range '+lo+'–'+hi+')':' · one run')+'</div>');});
    [0,5,10].forEach(function(v){txt(s,X(v),rows.length*rh+16,v,{"text-anchor":"middle","class":"t-mono t-mut","font-size":"9"});});
  },"the coherence arm of 40_ANALYTICAL_ARMS");

  card("Axiom nodes engaged, by layer","One dot per node the paper engages. Blue supports, darker is stated outright, red contests.",function(s){
    var nodes=X_.axiom_nodes||[];if(!nodes.length)return false;var modes=["AX_CORE","AX_DERIVED","AX_SCAFFOLD","FW_EXTENDED","HY_EVIDENCE"];
    var kinds={directly_asserted:["stated outright",css("--q4")],supported:["supported",css("--q2")],relevant_but_not_asserted:["relevant only",css("--mid")],contested:["contested",css("--b2")]};
    var L=100,rh=30;s.setAttribute("viewBox","0 0 340 "+(modes.length*rh+36));
    modes.forEach(function(m,i){var y=i*rh+14;txt(s,L-8,y+4,m,{"text-anchor":"end","class":"t-mono","font-size":"10"});
      nodes.filter(function(n){return n.mode===m;}).forEach(function(n,k){var kk=kinds[n.alignment]||kinds.relevant_but_not_asserted;var c=el("circle",{cx:L+6+k*15,cy:y,r:5.5,fill:kk[1],stroke:sur,"stroke-width":1.5},s);hover(c,'<div class="t1">'+(n.node||m)+'</div><div class="t2">'+kk[0]+'</div>');});});
    Object.keys(kinds).forEach(function(k,i){var x=8+i*84;el("circle",{cx:x+5,cy:modes.length*rh+24,r:5,fill:kinds[k][1]},s);txt(s,x+14,modes.length*rh+28,kinds[k][0],{"font-size":"10"});});
  },"the axiom-nodes arm of 40_ANALYTICAL_ARMS");

  card("Sentence lengths","Every sentence as a tick, with the middle half boxed. The dashed line is your corpus median.",function(s){
    var ls=(X_.sentence_lengths||[]).slice();if(!ls.length)return false;ls.sort(function(a,b){return a-b;});var n=ls.length,top=Math.max(40,ls[n-1]);
    s.setAttribute("viewBox","0 0 340 120");var L=10,W=320;var X=function(v){return L+v/top*W;};
    var q1=ls[Math.floor(n*.25)],q2=ls[Math.floor(n*.5)],q3=ls[Math.floor(n*.75)];
    el("rect",{x:X(q1),y:22,width:X(q3)-X(q1),height:44,fill:css("--wash"),stroke:ax},s);
    ls.forEach(function(v,i){var j=(i*53)%28;el("line",{x1:X(v),x2:X(v),y1:30+j,y2:34+j,stroke:s1,"stroke-opacity":.5,"stroke-width":1.4},s);});
    el("line",{x1:X(q2),x2:X(q2),y1:18,y2:70,stroke:ink,"stroke-width":2},s);
    if(typeof CM["Mean words per sentence"]==="number")el("line",{x1:X(CM["Mean words per sentence"]),x2:X(CM["Mean words per sentence"]),y1:12,y2:76,stroke:mu,"stroke-width":1.5,"stroke-dasharray":"4 3"},s);
    txt(s,X(q2),12,"median "+q2,{"text-anchor":"middle","class":"t-ink t-mono","font-size":"10"});
    [0,Math.round(top/2),top].forEach(function(v){txt(s,X(v),94,v,{"text-anchor":"middle","class":"t-mono t-mut","font-size":"9"});});
    txt(s,L+W/2,110,"words per sentence",{"text-anchor":"middle","font-size":"10"});
  },"station 42");

  card("Emotional arc","Rolling tone across the paper (9-sentence window).",function(s){
    var tn=X_.tone||[];var n=tn.length;if(n<3)return false;
    s.setAttribute("viewBox","0 0 340 170");var L=26,T=10,W=304,H=130;var X=function(i){return L+i/(n-1)*W;},Y=function(v){return T+H/2-clamp(v,-1.2,1.2)*H/2.4;};
    el("line",{x1:L,x2:L+W,y1:Y(0),y2:Y(0),stroke:ax},s);
    var pts=[];for(var i=0;i<n;i++){var w=0,c=0;for(var k=Math.max(0,i-4);k<=Math.min(n-1,i+4);k++){w+=tn[k];c++;}pts.push([X(i),Y(w/c)]);}
    el("path",{d:"M"+X(0)+" "+Y(0)+" L"+pts.map(function(p){return p.join(" ");}).join(" L")+" L"+X(n-1)+" "+Y(0)+" Z",fill:s1,"fill-opacity":.12},s);
    el("path",{d:"M"+pts.map(function(p){return p.join(" ");}).join(" L"),fill:"none",stroke:s1,"stroke-width":2},s);
    [1,Math.round(n/2),n].forEach(function(k){txt(s,X(k-1),T+H+16,"S"+k,{"text-anchor":"middle","class":"t-mono t-mut","font-size":"9"});});
  },"station 42 (sentence tone)");

  card("Where it sits in its series","Each row: this paper's percentile within its series on one statistic.",function(s){
    var rows=METRICS.filter(function(m){return typeof m.series==="number";}).slice(0,8);if(!rows.length)return false;
    var L=150,W=170,rh=26;s.setAttribute("viewBox","0 0 340 "+(rows.length*rh+22));var X=function(v){return L+v/100*W;};
    rows.forEach(function(m,i){var y=i*rh+13;txt(s,L-8,y+4,m.name,{"text-anchor":"end","font-size":"10"});el("line",{x1:L,x2:L+W,y1:y,y2:y,stroke:gr},s);
      var c=el("circle",{cx:X(m.series),cy:y,r:5.5,fill:s1,stroke:sur,"stroke-width":2},s);hover(c,'<div class="t1">'+m.name+'</div><div class="t2">'+ord(m.series)+' within the series</div>');});
    [0,50,100].forEach(function(v){txt(s,X(v),rows.length*rh+16,v+"th",{"text-anchor":"middle","class":"t-mono t-mut","font-size":"9"});});
  },"other papers in the same series with a 42 run");
}

'''


def between(text: str, start: str, end: str, new: str, keep_end: bool = True) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + new + (text[b:] if keep_end else text[b + len(end):])


def main() -> None:
    html = SRC.read_text(encoding="utf-8")
    html = between(html, "/* ---------- deterministic demo data ---------- */", "var N=METRICS.length;", DATA, keep_end=False)
    html = between(html, "function find(fk,name)", "/* ---------- matrix ---------- */", TILES)
    html = between(html, "/* ---------- specialised charts ---------- */", "/* ---------- the wall ---------- */", CHARTS)
    html = html.replace("function famGood(fi,frame){var s=0,n=0;METRICS.forEach(function(m){if(m.fam===fi){var g=frame===\"co\"?m.gc:m.ga;if(g!=null){s+=g;n++;}}});return n?s/n:null;}",
                        "function famGood(fi,frame){var s=0,n=0;METRICS.forEach(function(m){if(m.fam===fi){var g=frame===\"co\"?(m.gcKnown?m.gc:null):m.ga;if(g!=null){s+=g;n++;}}});return n?s/n:(frame===\"co\"?50:null);}")
    html = html.replace("DEMO NUMBERS · generated to show the layout, not a real run", "LIVE DATA · __LIVE_TITLE__")
    html = html.replace("Every number on this page is generated demo data.",
                        "Every number comes from statistics.json (station 42) and the station runs it cites; hover a circle for its method.")
    html = html.replace('<h1 id="paperTitle">The Resurrection as Information Preserved</h1>', '<h1 id="paperTitle">__LIVE_TITLE__</h1>')
    html = html.replace("Paper statistics · information matrix · prototype", "Paper statistics · information matrix")
    html = html.replace("<title>Paper Information Matrix</title>", "<title>Statistics: __LIVE_TITLE__</title>")
    html = html.replace("Prototype for the Statistics Wall spec (STATISTICS_WALL_V1). ", "Statistics Wall (STATISTICS_WALL_V1), approved matrix design. ")
    html = html.replace("<b>What this demo paper shows.</b>", "<b>What this paper shows.</b>")
    html = html.replace("var gap=rows.filter(function(r){return r.ac!=null;}).sort(function(a,b){return (b.co-b.ac)-(a.co-a.ac);})[0];",
                        "var gap=rows.filter(function(r){return r.ac!=null;}).sort(function(a,b){return (b.co-b.ac)-(a.co-a.ac);})[0]||{n:\"(no academic benchmarks set yet)\",co:0,ac:0};")
    html = html.replace("<b>9</b> scopes (whole paper + 8 sections)", "<b>1</b> scope (whole paper; sections come later)")
    html = html.replace("'<div class=\"t2\">'+(m.src===\"A\"?'AI-judged':'computed locally')+(m.low?' · runs disagreed':'')+' · |z| '+m.z.toFixed(2)+'</div>';}",
                        "'<div class=\"t2\">'+(m.src===\"A\"?'AI-judged':'computed locally')+(m.low?' · runs disagreed':'')+' · |z| '+m.z.toFixed(2)+'</div><div class=\"t2\">method: '+m.method+' · corpus n='+m.cn+'</div>';}")
    for marker in ("__LIVE_PAYLOAD__", "__LIVE_TITLE__"):
        assert marker in html, marker
    assert "The Resurrection as Information Preserved" not in html, "demo title left"
    assert "rng(20260925)" not in html and "nrm()" not in html.split("/* ---------- live data")[1], "demo generator still referenced"
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
