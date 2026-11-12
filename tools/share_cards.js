var ZH=/^zh/.test(document.documentElement.lang||'');
if(ZH){(function(){
var F='"Noto Serif SC","Noto Serif JP","Noto Serif",serif',W=1080,H=1350,KIND='he',CN=D.c||'',TOTAL=498;
var TABS=[['he','格物卡'],['bing','内圣卡'],['long','外王卡']];
function RD(){try{return JSON.parse(localStorage.getItem('yk_rd')||'[]')||[]}catch(e){return []}}
function WR(a){try{localStorage.setItem('yk_rd',JSON.stringify(a))}catch(e){}}
function today(){var t=new Date();return t.getFullYear()+'-'+('0'+(t.getMonth()+1)).slice(-2)+'-'+('0'+t.getDate()).slice(-2)}
function sents(){return [].slice.call(document.querySelectorAll('.yuanwen blockquote .ju')).map(function(s){return s.textContent})}
function rows(){try{var z=document.querySelector('.zjdata');return z?JSON.parse(z.textContent):[]}catch(e){return []}}
function strip(t){return t.replace(/^[^，。：；？！]{1,8}(曰|问|对曰|问曰)：/,'')}
function keyIdx(){var S=sents(),k=D.kn;if(typeof k==='number'&&S[k-1])return k;if(typeof k==='string'){for(var i=0;i<S.length;i++)if(S[i].indexOf(k)>=0)return i+1}
  for(var j=0;j<S.length;j++)if(strip(S[j]).replace(/[，。；：？！、“”‘’「」]/g,'').length>=4)return j+1;return 1}
function bhAll(){var p=document.querySelector('.sec-白 p');return p?p.textContent.trim():''}
function keyBh(kn){var R=rows(),b=(R[kn-1]||{}).bh||'',S=sents();if(b)return b;var a=bhAll();if(S.length===1||a.length<=48)return a;return ''}
function fit(c,t,w,sizes,maxH,lh,weight){for(var i=0;i<sizes.length;i++){c.font=(weight||700)+' '+sizes[i]+'px '+F;var L=wrap(c,t,w);if(L.length*sizes[i]*lh<=maxH)return{s:sizes[i],L:L}}c.font=(weight||700)+' '+sizes[sizes.length-1]+'px '+F;return{s:sizes[sizes.length-1],L:wrap(c,t,w)}}
function frame(c){c.fillStyle='#F2F1EA';c.fillRect(0,0,W,H);c.strokeStyle='#23503F';c.lineWidth=2;c.strokeRect(29,29,W-58,H-58)}
function foot(c,seal,label,url){var y=H-76;if(seal)c.drawImage(seal,84,y-64,64,64);c.textBaseline='alphabetic';c.fillStyle='#23503F';c.font='700 34px '+F;c.fillText('一孔录',164,y-30);c.fillStyle='#8A5A2C';c.font='400 22px '+F;c.fillText('逐字读经典原文',164,y);
  var q=qrcode(0,'M');q.addData(url);q.make();var n=q.getModuleCount(),cs=Math.max(2,Math.floor(150/n)),qs=cs*n,qx=W-84-qs,qy=y-qs;c.fillStyle='#fff';c.fillRect(qx-8,qy-8,qs+16,qs+16);c.strokeStyle='#ccc';c.lineWidth=1;c.strokeRect(qx-8.5,qy-8.5,qs+17,qs+17);c.fillStyle='#1E2A25';
  for(var r=0;r<n;r++)for(var k=0;k<n;k++)if(q.isDark(r,k))c.fillRect(qx+k*cs,qy+r*cs,cs,cs);
  c.textAlign='right';c.fillStyle='#23503F';c.font='700 26px '+F;c.fillText(label,qx-30,y-46);c.fillStyle='#999';c.font='400 21px '+F;c.fillText(D.u.replace(/^https:\/\//,'').replace(/\.html$/,''),qx-30,y-12);c.textAlign='left'}
function loadSeal(cb){var s=new Image();s.onload=function(){cb(s)};s.onerror=function(){cb(null)};s.src='/assets/seal-180.png'}
function fonts(t){return Promise.all(['700 96px '+F,'400 30px '+F,'700 200px '+F].map(function(f){return document.fonts?document.fonts.load(f,t).catch(function(){}):0}))}
function cols(kn){var out=[];document.querySelectorAll('.yuanwen.dz .yyp').forEach(function(a){var sv=a.querySelector('svg'),im=a.querySelector('image');if(!sv||!im)return;var vb=sv.getAttribute('viewBox').split(' ').map(Number),pw=+im.getAttribute('width');
  var rs=[].slice.call(a.querySelectorAll('rect.hl')).filter(function(r){return r.dataset.s==kn}).map(function(r){return['x','y','width','height'].map(function(k){return +r.getAttribute(k)})});rs.sort(function(p,q){return q[0]-p[0]});
  rs.forEach(function(r){out.push({src:im.getAttribute('href'),pw:pw,y0:vb[1],y1:vb[1]+vb[3],p:+a.dataset.p.slice(1),r:r})})});
  if(out.length>2)out=out.slice(0,1);var G=[];out.forEach(function(o){var g=G.length&&G[G.length-1].src===o.src?G[G.length-1]:null;if(!g){g={src:o.src,pw:o.pw,y0:o.y0,y1:o.y1,p:o.p,rs:[]};G.push(g)}g.rs.push(o.r)});
  G.forEach(function(g){var x0=1e9,x1=0,cw=0;g.rs.forEach(function(r){x0=Math.min(x0,r[0]);x1=Math.max(x1,r[0]+r[2]);cw=Math.max(cw,r[2])});var pad=cw*0.5;g.x0=Math.max(0,x0-pad);g.x1=Math.min(g.pw,x1+pad)});return G}
function he(){if(HT&&VT)return heV();var kn=keyIdx(),S=sents(),key=strip(S[kn-1]||D.y),bh=keyBh(kn),G=cols(kn);
  Promise.all([fonts(D.h+key+bh+'一孔录逐字读经典原文扫码读懂这一章朱熹《论语集注》四部备要本原页0123456789'),new Promise(function(ok){qr(ok)})].concat(G.map(function(g){return new Promise(function(ok){var m=new Image();m.crossOrigin='anonymous';m.onload=function(){g.im=m;ok()};m.onerror=function(){ok()};m.src=g.src})}))).then(function(){
  G=G.filter(function(g){return g.im});var cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');frame(c);
  var IH=940,GAP=12,IW=500,sc=0,iw=0;if(G.length){var th=0,tw=0;G.forEach(function(g){th=Math.max(th,g.y1-g.y0);tw+=g.x1-g.x0});sc=IH/th;var need=(IW-GAP*(G.length-1))/sc-tw;if(need>0)G.forEach(function(g){var e=need/G.length/2,a=g.x0-e,b=g.x1+e;if(a<0){b-=a;a=0}if(b>g.pw){a-=b-g.pw;b=g.pw}g.x0=Math.max(0,a);g.x1=b});tw=0;G.forEach(function(g){tw+=g.x1-g.x0});tw=tw*sc+GAP*(G.length-1);if(tw>IW){sc=sc*IW/tw;tw=IW}iw=tw}
  var right=W-110,ix=right-iw,iy=84,leftW=G.length?Math.min(620,ix-84-50):W-168;
  loadSeal(function(seal){c.textBaseline='alphabetic';c.fillStyle='#8A5A2C';c.font='400 26px '+F;c.fillText(D.h,84,96+26);
    var bare=key.replace(/[，。；：？！、“”‘’「」]/g,''),ww=bare.length<=16&&G.length?Math.min(leftW,96*4.6):leftW;
    var vh=0,VL=[];if(bh){c.font='400 30px '+F;VL=wrap(c,bh,leftW);if(VL.length>5){VL=VL.slice(0,5);VL[4]=VL[4].slice(0,-1)+'……'}vh=VL.length*54+88}
    var ft=fit(c,key,ww,[96,88,80,72,64,58,52,46,40],(G.length?1000:1080)-250-vh,1.45,700),y=250;c.fillStyle='#1a1a1a';
    ft.L.forEach(function(l){c.fillText(l,84,y+ft.s);y+=ft.s*1.45});
    if(VL.length){y+=40;c.fillStyle='#23503F';c.fillRect(84,y,64,4);y+=32;c.fillStyle='#555';c.font='400 30px '+F;VL.forEach(function(l){c.fillText(l,84,y+30);y+=54})}
    if(G.length){var x=right;c.save();c.shadowColor='rgba(0,0,0,.18)';c.shadowBlur=30;c.shadowOffsetY=6;c.fillStyle='#fff';c.fillRect(ix,iy,iw,IH);c.restore();
      G.forEach(function(g,k){var k2=g.im.naturalWidth/g.pw,gw=(g.x1-g.x0)*sc,gh=(g.y1-g.y0)*sc;x-=gw;c.drawImage(g.im,g.x0*k2,g.y0*k2,(g.x1-g.x0)*k2,(g.y1-g.y0)*k2,x,iy,gw,gh);
        c.strokeStyle='#C0392B';c.lineWidth=4;g.rs.forEach(function(r){c.strokeRect(x+(r[0]-g.x0)*sc,iy+(r[1]-g.y0)*sc,r[2]*sc,r[3]*sc)});if(k<G.length-1){x-=GAP;c.fillStyle='#F2F1EA';c.fillRect(x,iy,GAP,IH)}});
      var ps=G.map(function(g){return g.p}),pl=ps[0]+(ps.length>1&&ps[1]!==ps[0]?'—'+ps[ps.length-1]:'');c.fillStyle='#999';c.font='400 22px '+F;c.textAlign='right';c.fillText('朱熹《论语集注》四部备要本 · 原页 '+pl,right,iy+IH+42);c.textAlign='left'}
    foot(c,seal,'扫码读懂这一章',D.u+'?f=he');show(cv)})})}

// 直排格物卡（11-09 主人：繁体页给格物卡加直排选项，横排仍默认）
var VT=(function(){try{return localStorage.getItem('yk_vt')==='1'}catch(e){return false}})();
var VROT='「」『』（）《》〈〉—…～-',VPUN='，。、．',VMID='：；！？';
function vcols(t,n){var C=[],cur=[];var T=QQ(t).replace(/\s+/g,'').match(/[0-9]{1,3}|[\s\S]/g)||[];for(var i=0;i<T.length;i++){var ch=T[i];if(cur.length>=n){if((VPUN+VMID+'」』）》〉').indexOf(ch)>=0){cur.push(ch);C.push(cur);cur=[];continue}C.push(cur);cur=[]}cur.push(ch)}if(cur.length)C.push(cur);return C}
function vfit(t,sizes,hgt,maxW,gap){for(var i=0;i<sizes.length;i++){var s=sizes[i],n=Math.floor(hgt/(s*1.08)),C=vcols(t,n),w=C.length*s*gap;if(w<=maxW)return{s:s,C:C,w:w}}var s2=sizes[sizes.length-1];var C2=vcols(t,Math.floor(hgt/(s2*1.08)));return{s:s2,C:C2,w:C2.length*s2*gap}}
function vdraw(c,C,xr,y0,s,gap){c.textAlign='center';c.textBaseline='middle';C.forEach(function(col,j){var cx=xr-j*s*gap-s/2,y=y0;col.forEach(function(ch){var cy=y+s*0.54;
  if(VROT.indexOf(ch)>=0){c.save();c.translate(cx,cy);c.rotate(Math.PI/2);c.fillText(ch,0,0);c.restore()}
  else if((VPUN+VMID).indexOf(ch)>=0){c.textAlign='left';c.textBaseline='alphabetic';var mm=c.measureText(ch),gx=(mm.actualBoundingBoxRight-mm.actualBoundingBoxLeft)/2,gy=(mm.actualBoundingBoxDescent-mm.actualBoundingBoxAscent)/2;c.textAlign='left';c.textBaseline='alphabetic';c.fillText(ch,cx-gx,cy-gy);c.textAlign='center';c.textBaseline='middle'}
  else c.fillText(ch,cx,cy);y+=s*1.08})});c.textAlign='left';c.textBaseline='alphabetic'}
function heV(){var kn=keyIdx(),S=sents(),key=strip(S[kn-1]||D.y),bh=keyBh(kn),G=cols(kn);
  Promise.all([fonts(D.h+key+bh+'一孔录逐字读经典原文扫码读懂这一章朱熹《论语集注》四部备要本原页0123456789「」，。'),new Promise(function(ok){qr(ok)})].concat(G.map(function(g){return new Promise(function(ok){var m=new Image();m.crossOrigin='anonymous';m.onload=function(){g.im=m;ok()};m.onerror=function(){ok()};m.src=g.src})}))).then(function(){
  G=G.filter(function(g){return g.im});var cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');frame(c);
  var TOP=96,BOT=H-300,HG=BOT-TOP,IW=G.length?360:0,GAP=12,sc=0,iw=0;
  if(G.length){var th=0,tw=0;G.forEach(function(g){th=Math.max(th,g.y1-g.y0);tw+=g.x1-g.x0});sc=HG/th;var need=(IW-GAP*(G.length-1))/sc-tw;if(need>0)G.forEach(function(g){var e=need/G.length/2,a=g.x0-e,b=g.x1+e;if(a<0){b-=a;a=0}if(b>g.pw){a-=b-g.pw;b=g.pw}g.x0=Math.max(0,a);g.x1=b});tw=0;G.forEach(function(g){tw+=g.x1-g.x0});tw=tw*sc+GAP*(G.length-1);if(tw>IW){sc=sc*IW/tw;tw=IW}iw=tw}
  loadSeal(function(seal){var xr=W-84;
    c.fillStyle='#8A5A2C';c.font='400 26px '+F;vdraw(c,vcols(D.h,99),xr,TOP+4,26,1.5);xr-=26*1.5+34;
    var avail=xr-84-(iw?iw+56:0),bf=null,bw=0;
    if(bh){var bt=bh;c.font='400 30px '+F;bf=vfit(bt,[30],HG,avail*0.45,1.75);if(bf.w>avail*0.45){var n=Math.floor(HG/(30*1.08)),mx=Math.max(1,Math.floor(avail*0.45/(30*1.75)));bf.C=bf.C.slice(0,mx);var lc=bf.C[mx-1];lc.splice(Math.max(0,lc.length-2),2,'…','…');bf.w=mx*30*1.75}bw=bf.w+56}
    var kf=vfit(key,[96,88,80,72,64,58,52,46,40],HG,avail-bw,1.4);
    c.fillStyle='#1a1a1a';c.font='700 '+kf.s+'px '+F;vdraw(c,kf.C,xr,TOP,kf.s,1.4);xr-=kf.w;
    if(bf){xr-=28;c.fillStyle='#23503F';c.fillRect(xr-4,TOP,4,64);xr-=28;c.fillStyle='#555';c.font='400 30px '+F;vdraw(c,bf.C,xr,TOP,30,1.75);xr-=bf.w}
    if(G.length){var ix=84,iy=TOP,x=ix+iw;c.save();c.shadowColor='rgba(0,0,0,.18)';c.shadowBlur=30;c.shadowOffsetY=6;c.fillStyle='#fff';c.fillRect(ix,iy,iw,HG);c.restore();
      G.forEach(function(g,k){var k2=g.im.naturalWidth/g.pw,gw=(g.x1-g.x0)*sc,gh=(g.y1-g.y0)*sc;x-=gw;c.drawImage(g.im,g.x0*k2,g.y0*k2,(g.x1-g.x0)*k2,(g.y1-g.y0)*k2,x,iy,gw,gh);
        c.strokeStyle='#C0392B';c.lineWidth=4;g.rs.forEach(function(r){c.strokeRect(x+(r[0]-g.x0)*sc,iy+(r[1]-g.y0)*sc,r[2]*sc,r[3]*sc)});if(k<G.length-1){x-=GAP;c.fillStyle='#F2F1EA';c.fillRect(x,iy,GAP,HG)}});
      var ps=G.map(function(g){return g.p}),pl=ps[0]+(ps.length>1&&ps[1]!==ps[0]?'—'+ps[ps.length-1]:'');c.fillStyle='#999';c.font='400 22px '+F;c.fillText('朱熹《论语集注》四部备要本 · 原页 '+pl,ix,iy+HG+40)}
    foot(c,seal,'扫码读懂这一章',D.u+'?f=he');show(cv)})})}
function bing(){var R=RD(),td=today(),set={},days=0,chs={},nz=0;R.forEach(function(r){set[r.d]=1;if(!chs[r.c]){chs[r.c]=1;nz+=r.n||0}});var nc=Object.keys(chs).length;
  for(var t=new Date();;t.setDate(t.getDate()-1)){var k=t.getFullYear()+'-'+('0'+(t.getMonth()+1)).slice(-2)+'-'+('0'+t.getDate()).slice(-2);if(set[k])days++;else if(k!==td)break;else if(!set[k])break;if(days>4000)break}
  var cn=(CN.split('.')[1]||''),S=sents(),txt=D.y.length<=40?D.y:strip(S[keyIdx()-1]||D.y),bh=bhAll();if(bh.length>48)bh=keyBh(keyIdx());
  var now=new Date(),RL=rili(),jq=RL&&/^今日/.test(RL.jq)?' · '+RL.jq.split(' · ')[0]:'',dl=(now.getMonth()+1)+'月'+now.getDate()+'日 · 星期'+'日一二三四五六'[now.getDay()]+jq,side=days>=2?'读经第 '+days+' 天':'累计读了 '+nc+' 章';
  Promise.all([fonts(dl+side+txt+bh+'第章我在逐字读《论语》全书已读字已有位儒者在共读今天这一章扫码一起读一孔录逐字读经典原文0123456789,'),new Promise(function(ok){qr(ok)})]).then(function(){
  var cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');frame(c);
  loadSeal(function(seal){c.textBaseline='alphabetic';c.fillStyle='#8A5A2C';c.font='400 26px '+F;c.fillText(dl,84,122);c.textAlign='right';c.fillText('我在逐字读《论语》',W-84,122);var gt=+window.yklTotal||0;if(gt>=10){c.fillStyle='#23503F';c.font='700 28px '+F;c.fillText('已有 '+gt.toLocaleString('en')+' 位儒者在共读《论语》',W-84,170)}c.textAlign='left';
    var big='第'+cn+'章',bs=200;c.font='700 '+bs+'px '+F;while(c.measureText(big).width>W-168-260&&bs>120){bs-=10;c.font='700 '+bs+'px '+F}c.fillStyle='#23503F';c.fillText(big,84,230+bs*0.86);var bw=c.measureText(big).width;
    c.fillStyle='#8A5A2C';c.font='400 40px '+F;c.fillText(side,84+bw+24,230+bs*0.86);
    var py=230+bs+30;c.fillStyle='#DDDACB';c.beginPath();if(c.roundRect)c.roundRect(84,py,W-168,14,7);else c.rect(84,py,W-168,14);c.fill();var pw=Math.max(14,(W-168)*Math.min(1,nc/TOTAL));c.fillStyle='#23503F';c.beginPath();if(c.roundRect)c.roundRect(84,py,pw,14,7);else c.rect(84,py,pw,14);c.fill();
    c.fillStyle='#999';c.font='400 24px '+F;c.fillText('全书 '+TOTAL+' 章 · 已读 '+nc+' 章 · '+nz.toLocaleString('en')+' 字',84,py+14+38);
    var y=py+14+38+80;c.fillStyle='#23503F';c.fillRect(84,y,64,4);y+=40;c.fillStyle='#8A5A2C';c.font='400 26px '+F;c.fillText('今天这一章 · '+D.h,84,y+26);y+=26+40;
    var ft=fit(c,txt,W-168,[72,64,58,52,46,40],H-76-200-y-(bh?110:0),1.5,700);c.fillStyle='#1a1a1a';ft.L.forEach(function(l){c.fillText(l,84,y+ft.s);y+=ft.s*1.5});
    if(bh){y+=20;c.fillStyle='#777';c.font='400 28px '+F;wrap(c,bh,W-168).slice(0,3).forEach(function(l){c.fillText(l,84,y+28);y+=50})}
    foot(c,seal,'扫码一起读',D.u+'?f=bing');show(cv)})})}
var show0=show;show=function(cv){show0(cv);var M=document.querySelectorAll('.shmodal'),m=M[M.length-1];if(!m)return;var box=m.querySelector('.shm'),bar=document.createElement('div');bar.className='shtabs';
  TABS.forEach(function(t){var b=document.createElement('button');b.type='button';b.textContent=t[1];if(t[0]===KIND)b.className='on';b.onclick=function(){m.remove();if(t[0]==='bing')window.ykBing();else pick(t[0])};bar.appendChild(b)});box.insertBefore(bar,box.firstChild);
  if(KIND==='he'&&HT){var vb=document.createElement('div');vb.className='shtabs shvt';[['0','橫排'],['1','直排']].forEach(function(o){var b=document.createElement('button');b.type='button';b.textContent=o[1];if((VT?'1':'0')===o[0])b.className='on';b.onclick=function(){VT=o[0]==='1';try{localStorage.setItem('yk_vt',VT?'1':'0')}catch(e){}m.remove();he()};vb.appendChild(b)});box.insertBefore(vb,bar.nextSibling)}
  if(KIND==='bing'){var nt=document.createElement('p');nt.className='note shrec';nt.textContent='读过的章记在这台设备上。换手机或电脑时，先导出一串记录码，到新设备上粘进去恢复。';var bx=document.createElement('div');bx.className='shmb';
    var ex=document.createElement('button');ex.type='button';ex.className='btn ghost';ex.textContent='导出记录';ex.onclick=function(){var code='YK1.'+btoa(unescape(encodeURIComponent(JSON.stringify(RD().map(function(r){return[r.d,r.c,r.n||0]})))));
      if(navigator.clipboard)navigator.clipboard.writeText(code).then(function(){ex.textContent='已复制记录码'},function(){prompt('记录码',code)});else prompt('记录码',code)};
    var im=document.createElement('button');im.type='button';im.className='btn ghost';im.textContent='恢复记录';im.onclick=function(){var s=prompt('粘贴记录码');if(!s)return;try{var a=JSON.parse(decodeURIComponent(escape(atob(s.trim().replace(/^YK1\./,''))))),cur=RD(),seen={};cur.forEach(function(r){seen[r.d+'|'+r.c]=1});
      a.forEach(function(x){if(!seen[x[0]+'|'+x[1]])cur.push({d:x[0],c:x[1],n:x[2]})});cur.sort(function(p,q){return p.d<q.d?-1:1});WR(cur);m.remove();pick('bing')}catch(e){alert('记录码不对')}};
    bx.appendChild(ex);bx.appendChild(im);box.appendChild(nt);box.appendChild(bx)}};
function pick(k){KIND=k;if(k==='he')he();else if(k==='bing')bing();else card()}
window.ykPick=pick;
window.ykBing=function(){var R=RD(),td=today();if(CN&&!R.some(function(r){return r.c===CN})){R.push({d:td,c:CN,n:D.y.replace(/[，。；：？！、“”‘’「」\s]/g,'').length});WR(R)}pick('bing')};
})()}
