var ZH=/^zh/.test(document.documentElement.lang||'');
var I=(function(){try{var e=document.querySelector('.sharebox .shi');return e?JSON.parse(e.textContent):{}}catch(e){return {}}})();
if(ZH||I.on){(function(){
var F='"Noto Serif SC","Noto Serif JP","Noto Serif KR","Noto Serif",serif',W=1080,H=1350,KIND='yy',CN=D.c||'',TOTAL=D.tot||498,BK=D.bk||'论语',SRC=D.src||'朱熹《论语集注》四部备要本',PF=D.pf||'';
var TABS=[['he','格物卡'],['bing','内圣卡'],['long','外王卡']];
function RD(){try{return JSON.parse(localStorage.getItem('yk_rd')||'[]')||[]}catch(e){return []}}
function WR(a){try{localStorage.setItem('yk_rd',JSON.stringify(a))}catch(e){}}
function today(){var t=new Date();return t.getFullYear()+'-'+('0'+(t.getMonth()+1)).slice(-2)+'-'+('0'+t.getDate()).slice(-2)}
function sents0(){return [].slice.call(document.querySelectorAll('.yuanwen blockquote .ju')).map(function(s){return s.textContent})}
var YY=D.yt||D.y,HZ=null;function hz(s){if(!D.yt||!s||D.yt.indexOf(s)>=0)return s;var i=D.y.indexOf(s);if(i>=0&&D.y.length===D.yt.length)return D.yt.substr(i,s.length);if(!HZ){HZ={};if(D.y.length===D.yt.length)for(var k=0;k<D.y.length;k++)if(!HZ[D.y[k]])HZ[D.y[k]]=D.yt[k]}return s.replace(/[\s\S]/g,function(c){return HZ[c]||c})}
function sents(){return sents0().map(hz)}
function rows(){try{var z=document.querySelector('.zjdata');return z?JSON.parse(z.textContent):[]}catch(e){return []}}
function strip(t){return t.replace(/^[^，。：；？！]{1,8}(曰|问|对曰|问曰)：/,'')}
function keyIdx(){var S=sents0(),k=D.kn;if(typeof k==='number'&&S[k-1])return k;if(typeof k==='string'){var k2=hz(k);for(var i=0;i<S.length;i++)if(S[i].indexOf(k)>=0||S[i].indexOf(k2)>=0)return i+1}
  for(var j=0;j<S.length;j++)if(strip(S[j]).replace(/[，。；：？！、“”‘’「」]/g,'').length>=4&&!(j<S.length-1&&/^[^，。：]{1,8}(问|請|请)[^，。：]{0,6}[。？]$/.test(S[j])))return j+1;return 1}
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
function he(){if(HT&&VT)return heV();var kn=keyIdx(),S=sents(),key=strip(S[kn-1]||YY),bh=keyBh(kn),G=cols(kn);
  Promise.all([fonts(D.h+key+bh+'一孔录逐字读经典原文扫码读懂这一章'+SRC+'原页0123456789'),new Promise(function(ok){qr(ok)})].concat(G.map(function(g){return new Promise(function(ok){var m=new Image();m.crossOrigin='anonymous';m.onload=function(){g.im=m;ok()};m.onerror=function(){ok()};m.src=g.src})}))).then(function(){
  G=G.filter(function(g){return g.im});var cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');frame(c);texture(c);
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
      var ps=G.map(function(g){return g.p}),pl=ps[0]+(ps.length>1&&ps[1]!==ps[0]?'—'+ps[ps.length-1]:'');c.fillStyle='#999';c.font='400 22px '+F;c.textAlign='right';c.fillText(SRC+' · 原页 '+pl,right,iy+IH+42);c.textAlign='left'}
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
function heV(){var kn=keyIdx(),S=sents(),key=strip(S[kn-1]||YY),bh=keyBh(kn),G=cols(kn);
  Promise.all([fonts(D.h+key+bh+'一孔录逐字读经典原文扫码读懂这一章'+SRC+'原页0123456789「」，。'),new Promise(function(ok){qr(ok)})].concat(G.map(function(g){return new Promise(function(ok){var m=new Image();m.crossOrigin='anonymous';m.onload=function(){g.im=m;ok()};m.onerror=function(){ok()};m.src=g.src})}))).then(function(){
  G=G.filter(function(g){return g.im});var cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');frame(c);texture(c);
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
      var ps=G.map(function(g){return g.p}),pl=ps[0]+(ps.length>1&&ps[1]!==ps[0]?'—'+ps[ps.length-1]:'');c.fillStyle='#999';c.font='400 22px '+F;c.fillText(SRC+' · 原页 '+pl,ix,iy+HG+40)}
    foot(c,seal,'扫码读懂这一章',D.u+'?f=he');show(cv)})})}
// 分享卡底纹（11-12 主人“分享卡看着还不错”，11-13 三张卡都用）：这一章全文的浅色小字铺满，卡面文字周围留白
function texture(c,w,h){w=w||W;h=h||H;var T=sents().join('').replace(/[^\u4e00-\u9fff]/g,'');if(!T)return;var i=0,cs=30;c.save();c.fillStyle='rgba(35,80,63,.065)';c.font='500 24px '+F;c.textAlign='center';c.textBaseline='middle';
  for(var y=72;y<h-66;y+=cs)for(var x=72;x<w-66;x+=cs){c.fillText(T.charAt(i%T.length),x,y);i++}c.restore();
  var f0=c.fillText;c.fillText=function(t,x,y){var st=c.strokeStyle,lw=c.lineWidth,lj=c.lineJoin;c.strokeStyle='#F2F1EA';c.lineWidth=Math.max(14,parseFloat(c.font.split(' ')[1])*.35);c.lineJoin='round';c.strokeText(t,x,y);c.strokeStyle=st;c.lineWidth=lw;c.lineJoin=lj;f0.call(c,t,x,y)}}
window.ykTex=texture;
function bing(){var R=RD(),td=today(),set={},days=0,chs={},nz=0;R.forEach(function(r){set[r.d]=1;if(!chs[r.c]&&(PF?String(r.c).indexOf(PF)===0:!/^[a-z]/.test(r.c))){chs[r.c]=1;nz+=r.n||0}});var nc=Object.keys(chs).length;
  for(var t=new Date();;t.setDate(t.getDate()-1)){var k=t.getFullYear()+'-'+('0'+(t.getMonth()+1)).slice(-2)+'-'+('0'+t.getDate()).slice(-2);if(set[k])days++;else if(k!==td)break;else if(!set[k])break;if(days>4000)break}
  var cn=(CN.split('.')[1]||''),S=sents(),txt=YY.length<=40?YY:strip(S[keyIdx()-1]||YY),bh=bhAll();if(bh.length>48)bh=keyBh(keyIdx());
  var now=new Date(),RL=rili(),jq=RL&&/^今日/.test(RL.jq)?' · '+RL.jq.split(' · ')[0]:'',dl=(now.getMonth()+1)+'月'+now.getDate()+'日 · 星期'+'日一二三四五六'[now.getDay()]+jq,side=days>=2?'读经第 '+days+' 天':'累计读了 '+nc+' 章';
  Promise.all([fonts(dl+side+txt+bh+'第章我在逐字读《'+BK+'》全书已读字已有位儒者在共读今天这一章扫码一起读一孔录逐字读经典原文0123456789,'),new Promise(function(ok){qr(ok)})]).then(function(){
  var cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');frame(c);texture(c);
  loadSeal(function(seal){c.textBaseline='alphabetic';c.fillStyle='#8A5A2C';c.font='400 26px '+F;c.fillText(dl,84,122);c.textAlign='right';c.fillText('我在逐字读《'+BK+'》',W-84,122);var gt=+window.yklTotal||0;if(gt>=10&&!D.bk){c.fillStyle='#23503F';c.font='700 28px '+F;c.fillText('已有 '+gt.toLocaleString('en')+' 位儒者在共读《论语》',W-84,170)}c.textAlign='left';
    var big='第'+cn+'章',bs=200;c.font='700 '+bs+'px '+F;while(c.measureText(big).width>W-168-260&&bs>120){bs-=10;c.font='700 '+bs+'px '+F}c.fillStyle='#23503F';c.fillText(big,84,230+bs*0.86);var bw=c.measureText(big).width;
    c.fillStyle='#8A5A2C';c.font='400 40px '+F;c.fillText(side,84+bw+24,230+bs*0.86);
    var py=230+bs+30;c.fillStyle='#DDDACB';c.beginPath();if(c.roundRect)c.roundRect(84,py,W-168,14,7);else c.rect(84,py,W-168,14);c.fill();var pw=Math.max(14,(W-168)*Math.min(1,nc/TOTAL));c.fillStyle='#23503F';c.beginPath();if(c.roundRect)c.roundRect(84,py,pw,14,7);else c.rect(84,py,pw,14);c.fill();
    c.fillStyle='#999';c.font='400 24px '+F;c.fillText('全书 '+TOTAL+' 章 · 已读 '+nc+' 章 · '+nz.toLocaleString('en')+' 字',84,py+14+38);
    var y=py+14+38+80;c.fillStyle='#23503F';c.fillRect(84,y,64,4);y+=40;c.fillStyle='#8A5A2C';c.font='400 26px '+F;c.fillText('今天这一章 · '+D.h,84,y+26);y+=26+40;
    var ft=fit(c,txt,W-168,[72,64,58,52,46,40],H-76-200-y-(bh?110:0),1.5,700);c.fillStyle='#1a1a1a';ft.L.forEach(function(l){c.fillText(l,84,y+ft.s);y+=ft.s*1.5});
    if(bh){y+=20;c.fillStyle='#777';c.font='400 28px '+F;wrap(c,bh,W-168).slice(0,3).forEach(function(l){c.fillText(l,84,y+28);y+=50})}
    foot(c,seal,'扫码一起读',D.u+'?f=bing');show(cv)})})}
// —— 11-14 四种分享卡（主人：原页、原创角色、全球多语、年历日期，各有鲜明特色）——
var X4=(function(){try{var e=document.querySelector('.sharebox .shx');return e?JSON.parse(e.textContent):{}}catch(e){return {}}})();
var LY=!PF&&/^\d+\.\d+$/.test(CN);
function LBL(){return LY?(ZH?(HT?'論語 ':'论语 '):I.lbl+' ')+CN:D.h}
function SHU(){return LY&&(ZH||I.sl)?'yikonglu.com/'+(ZH?(HT?'zh-hant/':''):I.lg+'/')+'lunyu/'+CN:D.u.replace(/^https:\/\//,'').replace(/\.html$/,'')}
function img(src){return new Promise(function(ok){if(!src){ok(null);return}var m=new Image();m.crossOrigin='anonymous';m.onload=function(){ok(m)};m.onerror=function(){ok(null)};m.src=src})}
function keyTxt(){var S=sents();return strip(S[keyIdx()-1]||YY)}
// 外文页：这一句的本语种译文（整章短就整章）
function myTr(){if(ZH)return '';var t=I.lg==='en'?X3.en:I.lg==='ja'?X3.ja:(X3.tr||{})[I.lg];t=t||D.r||'';if(!t)return '';var S=sents(),whole=YY.replace(/[，。；：？！、“”‘’「」\s]/g,'').length<=30;return (whole?t:(I.lg==='ja'&&jaPick(t,keyTxt()))||pickSent(t,keyIdx(),S.length)||t).trim()}
function wrapL(c,t,w){return I.lg==='ja'?wrap(c,t,w):wrapW(c,t,w)}
function rr(c,x,y,w,h,r){c.beginPath();if(c.roundRect)c.roundRect(x,y,w,h,r);else c.rect(x,y,w,h)}
// 统一页脚：一孔印＋站名＋CC BY 署名行；右边二维码、章号、短网址
function foot4(c,seal,dark,f){var y0=H-208,ink=dark?'#F2F1EA':'#23503F',sub=dark?'rgba(242,241,234,.62)':'#8A5A2C',gr=dark?'rgba(242,241,234,.45)':'#999';
  c.fillStyle=dark?'rgba(242,241,234,.22)':'rgba(35,80,63,.25)';c.fillRect(84,y0,W-168,2);
  var y=y0+48;if(seal)c.drawImage(seal,84,y,84,84);c.textBaseline='alphabetic';c.textAlign='left';
  c.fillStyle=ink;c.font='700 34px '+F;c.fillText('一孔录',186,y+36);c.fillStyle=sub;c.font='400 22px '+F;c.fillText(ZH?'逐字读经典原文':I.tag,186,y+70);
  c.fillStyle=gr;c.font='400 19px '+F;c.fillText(ZH?'CC BY 4.0 · 署名“一孔录”即可转载、商用':I.cc,84,H-52);
  var q=qrcode(0,'M');q.addData(D.u+'?f='+f);q.make();var n=q.getModuleCount(),cs=Math.max(2,Math.floor(132/n)),qs=cs*n,qx=W-84-qs,qy=y0+28;
  c.fillStyle='#fff';c.fillRect(qx-8,qy-8,qs+16,qs+16);c.fillStyle='#1E2A25';for(var r=0;r<n;r++)for(var k=0;k<n;k++)if(q.isDark(r,k))c.fillRect(qx+k*cs,qy+r*cs,cs,cs);
  c.textAlign='right';c.fillStyle=ink;c.font='700 36px '+F;c.fillText(LBL(),qx-30,qy+48);c.fillStyle=gr;c.font='400 21px '+F;c.fillText(SHU(),qx-30,qy+84);c.fillStyle=sub;c.font='400 20px '+F;c.fillText(ZH?'扫码读这一章':I.scan,qx-30,qy+118);c.textAlign='left'}
function prep(extra){return Promise.all([fonts(D.h+LBL()+extra+'一孔录逐字读经典原文扫码读这一章署名即可转载商用'+(ZH?'':I.tag+I.cc+I.scan)),new Promise(function(ok){qr(ok)}),new Promise(function(ok){loadSeal(ok)})]).then(function(a){return a[2]})}
function bfit(c,t,w,sizes,maxH,lh,weight){var r=fit(c,t,w,sizes,maxH,lh,weight);if(r.L.length>1){c.font=(weight||700)+' '+r.s+'px '+F;var n=r.L.length,tw=c.measureText(QQ(t)).width,w2=Math.min(w,tw/n*1.04);for(var i=0;i<12;i++){var L=wrap(c,t,w2);if(L.length<=n){r.L=L;break}w2+=r.s*0.5;if(w2>w)break}}return r}
function canvas(){var cv=document.createElement('canvas');cv.width=W;cv.height=H;return cv}

// 一、原页卡：底本原页占满画面，红框标出这一句
function yy(){var kn=keyIdx(),key=keyTxt(),G=cols(kn),g=G[0],TRL=myTr(),YS=ZH||PF?SRC:I.src;
  Promise.all([prep(key+YS+'原页第页'+TRL+(ZH?'':I.yy_h+I.yy_pg)),g?img(g.src):null]).then(function(a){var seal=a[0],im=a[1],cv=canvas(),c=cv.getContext('2d');
    var bg=c.createLinearGradient(0,0,0,H);bg.addColorStop(0,'#1B2621');bg.addColorStop(1,'#111815');c.fillStyle=bg;c.fillRect(0,0,W,H);
    c.fillStyle='#C9A46A';c.font='400 24px '+F;c.textBaseline='alphabetic';c.fillText((ZH?'原页':I.yy_h)+' · '+YS,84,92);c.textAlign='right';c.fillText(LBL(),W-84,92);c.textAlign='left';
    var bx=84,by=124,bw=W-168,bh=TRL?700:820;
    if(im&&g){var k2=im.naturalWidth/g.pw,ph=g.y1-g.y0,sc=bh/ph,vw=bw/sc,cx=(g.x0+g.x1)/2,x0=Math.max(0,Math.min(g.pw-vw,cx-vw/2));if(vw>g.pw){x0=0;vw=g.pw}var dw=vw*sc,dx=bx+(bw-dw)/2;
      c.save();c.shadowColor='rgba(0,0,0,.55)';c.shadowBlur=40;c.shadowOffsetY=10;c.fillStyle='#F2F1EA';c.fillRect(dx,by,dw,bh);c.restore();
      c.drawImage(im,x0*k2,g.y0*k2,vw*k2,ph*k2,dx,by,dw,bh);c.strokeStyle='#D63A2A';c.lineWidth=5;g.rs.forEach(function(r){c.strokeRect(dx+(r[0]-x0)*sc,by+(r[1]-g.y0)*sc,r[2]*sc,r[3]*sc)});
      c.fillStyle='rgba(242,241,234,.5)';c.font='400 20px '+F;c.textAlign='right';c.fillText(ZH?'第 '+g.p+' 页 · 红框是这一句':I.yy_pg.replace('{p}',g.p),bx+bw,by+bh+34);c.textAlign='left'}
    else{c.fillStyle='rgba(242,241,234,.06)';c.fillRect(bx,by,bw,bh)}
    var TL=[];if(TRL){c.font='400 28px '+F;TL=wrapL(c,TRL,W-168);if(TL.length>4){TL=TL.slice(0,4);TL[3]=TL[3].replace(/\s*\S{0,3}$/,'')+'…'}}
    var top=by+bh+64,ft=bfit(c,key,W-168,[60,54,48,42,38],H-208-top-30-(TL.length?TL.length*42+20:0),1.4,700),y=top;c.fillStyle='#F2F1EA';ft.L.forEach(function(l){c.fillText(l,84,y+ft.s);y+=ft.s*1.4});
    if(TL.length){y+=10;c.fillStyle='rgba(242,241,234,.72)';c.font='400 28px '+F;TL.forEach(function(l){c.fillText(l,84,y+28);y+=42})}
    foot4(c,seal,true,'yy');show(cv)})}

// 二、人物卡：一孔录原创角色（出场表里本章的人；没有就按章轮到谁）
function rw(){var who=(X4.who||[]).slice(0,1),key=keyTxt(),bh=ZH?keyBh(keyIdx()):myTr();if(!who.length){yy();return}
  if(!ZH)who=who.map(function(p){var t=(I.rw||{})[p[0]];return t?[p[0],t[0],'',t[1],'']:p});
  var names=who.map(function(p){return p[1]}).join(HT?'、':'、');
  Promise.all([prep(key+bh+names+who.map(function(p){return p[2]+(p[3]||'')+(p[4]||'')}).join('')+'一孔录原创角色读到这一句“”——論語錄'+(ZH?'':I.orig+I.reading))].concat(who.map(function(p){return img('https://img.yikonglu.com/gushi/img/'+p[0]+'-full.png')}))).then(function(a){var seal=a[0],ims=a.slice(1),cv=canvas(),c=cv.getContext('2d');
    var bg=c.createLinearGradient(0,0,0,H);bg.addColorStop(0,'#2C6A52');bg.addColorStop(.62,'#23503F');bg.addColorStop(1,'#1A3B2F');c.fillStyle=bg;c.fillRect(0,0,W,H);
    var gl=c.createRadialGradient(W*.72,H*.42,40,W*.72,H*.42,560);gl.addColorStop(0,'rgba(240,206,140,.42)');gl.addColorStop(1,'rgba(240,206,140,0)');c.fillStyle=gl;c.fillRect(0,0,W,H);
    var FB=H-212,fh=900;[1,0].forEach(function(i){var m=ims[i];if(!m)return;var s=(i===0?fh:fh*.86)/m.naturalHeight,w=m.naturalWidth*s,h=m.naturalHeight*s,x=i===0?W-w+60:W-w-110,yy2=FB-h;
      c.save();if(i>0)c.globalAlpha=.96;c.shadowColor='rgba(0,0,0,.35)';c.shadowBlur=30;c.drawImage(m,x,yy2,w,h);c.restore()});
    c.fillStyle='#F0CE8C';c.font='400 26px '+F;c.textBaseline='alphabetic';c.fillText(ZH?'一孔录原创角色':I.orig,84,104);
    c.fillStyle='#F2F1EA';c.font='700 46px '+F;c.fillText(names,84,170);
    var y=200;who.forEach(function(p){if(p[3]){c.font='700 30px '+F;var qt=p[3],L=ZH?wrap(c,qt,430):wrapL(c,qt,470);if(ZH&&L.length>1){var bst=null;qt.replace(/，/g,function(m,i){var A=qt.slice(0,i+1),B=qt.slice(i+1),wa=c.measureText(A).width,wb=c.measureText(B).width;if(wa<=470&&wb<=470&&(!bst||Math.abs(wa-wb)<bst[0]))bst=[Math.abs(wa-wb),[A,B]]});if(bst)L=bst[1];else{var P=qt.match(/[^，]+，?/g)||[];if(P.length<=3&&P.every(function(x){return c.measureText(x).width<=470}))L=P}}c.fillStyle='#F0CE8C';c.fillRect(84,y+6,4,L.length*44-10);c.fillStyle='#FFFFFF';L.forEach(function(l){c.fillText(l,102,y+30);y+=44});if(p[4]){c.font='400 20px '+F;c.fillStyle='rgba(242,241,234,.6)';c.fillText((HT?'—— 一孔錄《論語》':'—— 一孔录《论语》')+p[4],84,y+22);y+=34}else y+=8}
      else{c.font='400 21px '+F;var L=wrap(c,p[2],400);if(L.length>2){L=L.slice(0,2);L[1]=L[1].slice(0,-1)+'…'}c.fillStyle='rgba(242,241,234,.72)';L.forEach(function(l){c.fillText(l,84,y+21);y+=32});y+=6}});
    y+=50;c.fillStyle='#F0CE8C';c.fillRect(84,y,56,4);y+=40;c.fillStyle='#F0CE8C';c.font='400 24px '+F;c.fillText((ZH?'读到这一句':I.reading)+' · '+LBL(),84,y+24);y+=60;
    var ft=bfit(c,key,400,[72,64,58,52,46,40],FB-y-(bh?200:40),1.42,700);c.fillStyle='#FFFFFF';ft.L.forEach(function(l){c.fillText(l,84,y+ft.s);y+=ft.s*1.42});
    if(bh){y+=26;c.fillStyle='rgba(242,241,234,.78)';c.font='400 26px '+F;(ZH?wrap(c,bh,370):wrapL(c,bh,400)).slice(0,ZH?4:5).forEach(function(l){c.fillText(l,84,y+26);y+=44})}
    c.fillStyle='rgba(18,40,32,.9)';c.fillRect(0,H-212,W,212);foot4(c,seal,true,'rw');show(cv)})}

// 三、多语卡：一句原文居中，像石子落水一圈圈荡开，六种外语各占一格（11-14 改：备齐六种外语，重做版式）
var LGS=[['en','English','London · New York','A'],['ja','日本語','東京','あ'],['ko','한국어','서울','한'],['fr','Français','Paris','É'],['es','Español','Madrid · Ciudad de México','Ñ'],['ru','Русский','Москва','Я']];
function jaPick(t,key){var P=(t||'').match(/[^。？！]+[。？！]+」?/g);if(!P||P.length<2)return '';var K={};key.replace(/[一-鿿]/g,function(ch){K[ch]=1});var bi=-1,bs=0;P.forEach(function(x,i){var sc=0,seen={};x.replace(/[一-鿿]/g,function(ch){if(K[ch]&&!seen[ch]){seen[ch]=1;sc++}});if(sc>bs){bs=sc;bi=i}});if(bs<2)return '';var r=P[bi].trim();if(/「[^」]*$/.test(r))r=r.replace(/。$/,'')+'」';return r}
function pickSent(t,n,N){var P=(t||'').match(/[^.?!。？！]+[.?!。？！]+["”」』]?\s*/g);if(P&&N>1&&P.length===N+1)P=[P[0]+P[1]].concat(P.slice(2));if(P&&N>1&&P.length===N&&P[n-1])return P[n-1].trim();
  if(P&&N>1&&P.length>1){var S=sents().map(function(x){return x.replace(/\s/g,'').length}),tot=S.reduce(function(p,q){return p+q},0),a=0;for(var i=0;i<n-1;i++)a+=S[i];var b=(a+S[n-1])/tot;a=a/tot;
    var T=P.reduce(function(p,q){return p+q.length},0),cum=0,out='',best='',bo=0;P.forEach(function(x){var s0=cum/T,s1=(cum+x.length)/T,ov=Math.max(0,Math.min(b,s1)-Math.max(a,s0));if(ov>=(s1-s0)*.5)out+=x;if(ov>bo){bo=ov;best=x}cum+=x.length});return (out||best||t||'').trim().replace(/「([^」]*)$/,'「$1」')}return t||''}
function dy(){var S=sents(),kn=keyIdx(),key=keyTxt(),TR=X3.tr||{},rows=[],whole=YY.replace(/[，。；：？！、“”‘’「」\s]/g,'').length<=30;if(whole)key=strip(YY);
  var LG2=LGS.slice();if(!ZH){var me=LG2.filter(function(l){return l[0]===I.lg})[0],XL={de:['de','Deutsch','Berlin','Ä'],vi:['vi','Tiếng Việt','Hà Nội','Ư'],id:['id','Bahasa Indonesia','Jakarta','I']};if(me)LG2=[me].concat(LG2.filter(function(l){return l!==me}));else if(XL[I.lg]&&TR[I.lg])LG2=[XL[I.lg]].concat(LG2.slice(0,5))}
  LG2.forEach(function(l){var t=l[0]==='en'?X3.en:l[0]==='ja'?X3.ja:TR[l[0]];if(t)rows.push({n:l[1],city:l[2],gl:l[3],lg:l[0],t:whole?t:(l[0]==='ja'&&jaPick(t,key))||pickSent(t,kn,S.length)})});
  var HD=ZH?(HT?'一句話，'+(rows.length+1)+' 種語言':'一句话，'+(rows.length+1)+' 种语言'):I.dy_h.replace('{n}',rows.length+1);
  prep(key+HD+'原文中文北京'+(ZH?'':I.dy_orig)+rows.map(function(r){return r.n+r.city+r.gl+r.t}).join('')).then(function(seal){var cv=canvas(),c=cv.getContext('2d');
    c.fillStyle='#F2F1EA';c.fillRect(0,0,W,H);
    // 上半：墨绿水面，原文落在正中，金色涟漪一圈圈荡开，荡到下面六种语言里
    var cx=W/2,cy=292,HB0=520,bg=c.createRadialGradient(cx,cy,40,cx,cy,760);bg.addColorStop(0,'#2E6A53');bg.addColorStop(1,'#1A3B2F');c.fillStyle=bg;c.fillRect(0,0,W,HB0);
    c.save();c.beginPath();c.rect(0,0,W,HB0);c.clip();for(var i=1;i<=13;i++){var r=96+i*i*6+i*24;c.strokeStyle='rgba(240,206,140,'+Math.max(.05,.42-i*.03)+')';c.lineWidth=i%3===0?2.2:1.1;c.beginPath();c.arc(cx,cy,r,0,Math.PI*2);c.stroke()}c.restore();
    c.save();c.beginPath();c.rect(0,HB0,W,H-HB0-212);c.clip();for(var i=6;i<=13;i++){var r=96+i*i*6+i*24;c.strokeStyle='rgba(35,80,63,'+Math.max(.04,.16-(i-6)*.016)+')';c.lineWidth=i%3===0?2:1;c.beginPath();c.arc(cx,cy,r,0,Math.PI*2);c.stroke()}c.restore();
    c.textBaseline='alphabetic';c.textAlign='center';c.fillStyle='#F0CE8C';c.font='400 25px '+F;c.fillText(LBL()+' · '+HD,cx,82);
    c.font='900 72px '+F;var ft=bfit(c,key,W-220,[84,76,68,60,54,48],230,1.3,900),th=ft.L.length*ft.s*1.3,y=cy-th/2-ft.s*0.16;
    c.fillStyle='rgba(242,241,234,.7)';c.font='400 22px '+F;c.fillText(ZH?'原文 · 中文':I.dy_orig,cx,cy-th/2-34);
    c.save();c.shadowColor='rgba(0,0,0,.35)';c.shadowBlur=24;c.fillStyle='#FFFFFF';ft.L.forEach(function(l){c.font='900 '+ft.s+'px '+F;c.fillText(l,cx,y+ft.s);y+=ft.s*1.3});c.restore();
    c.textAlign='left';
    // 六格
    var gx=72,gy=HB0+36,gw=(W-gx*2-28)/2,gb=H-224,n=Math.ceil(rows.length/2),gh=(gb-gy-(n-1)*22)/n,pad=26,TW=gw-pad*2,HB=58,avail=gh-HB-pad;
    var FS=[30,28,26,24,22,21,20],pk=null;
    for(var z=0;z<FS.length;z++){var ok=true,LL=rows.map(function(r){c.font='400 '+FS[z]+'px '+F;var L=r.lg==='ja'?wrap(c,r.t,TW):wrapW(c,r.t,TW);if(L.length*FS[z]*1.42>avail)ok=false;return L});if(ok||z===FS.length-1){pk={s:FS[z],L:LL};break}}
    rows.forEach(function(r,i){var col=i%2,row=Math.floor(i/2),x=gx+col*(gw+28),y=gy+row*(gh+22);
      c.save();c.shadowColor='rgba(30,42,37,.10)';c.shadowBlur=18;c.shadowOffsetY=4;c.fillStyle='#FBFAF6';rr(c,x,y,gw,gh,14);c.fill();c.restore();
      c.strokeStyle='rgba(35,80,63,.14)';c.lineWidth=1;rr(c,x+.5,y+.5,gw-1,gh-1,14);c.stroke();
      c.save();rr(c,x,y,gw,gh,14);c.clip();c.fillStyle='rgba(35,80,63,.07)';c.font='900 200px '+F;c.textAlign='right';c.fillText(r.gl,x+gw-10,y+gh+30);c.restore();c.textAlign='left';
      c.fillStyle='#23503F';rr(c,x,y,8,gh,4);c.fill();
      c.fillStyle='#23503F';c.font='700 24px '+F;c.fillText(r.n,x+pad,y+40);c.textAlign='right';c.fillStyle='#A39A86';c.font='400 17px '+F;c.fillText(r.city,x+gw-pad,y+40);c.textAlign='left';
      c.fillStyle='rgba(138,90,44,.35)';c.fillRect(x+pad,y+HB-4,40,2);
      var L=pk.L[i],mx=Math.max(1,Math.floor(avail/(pk.s*1.42)));if(L.length>mx){L=L.slice(0,mx);L[mx-1]=L[mx-1].replace(/\s*\S{0,3}$/,'')+'…'}
      var ty=y+HB+6;c.fillStyle='#1E2A25';c.font='400 '+pk.s+'px '+F;L.forEach(function(l){c.fillText(l,x+pad,ty+pk.s);ty+=pk.s*1.42})});
    foot4(c,seal,false,'dy');show(cv)})}

// 四、年历卡：日期为主，《论语》年历这一天读这一章；带日历：星期、农历、节气与七十二候、节日（下一次轮到这一天的那一年，最早 2027 年）
var MON=['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月'];
function streak(){var R=RD(),set={},days=0,td=today();R.forEach(function(r){set[r.d]=1});for(var t=new Date();;t.setDate(t.getDate()-1)){var k=t.getFullYear()+'-'+('0'+(t.getMonth()+1)).slice(-2)+'-'+('0'+t.getDate()).slice(-2);if(set[k])days++;else break;if(days>4000)break}return days}
function lunar(dt){try{var o={};new Intl.DateTimeFormat('zh-CN-u-ca-chinese',{year:'numeric',month:'numeric',day:'numeric'}).formatToParts(dt).forEach(function(p){o[p.type]=p.value});
  var ms=(o.month||'').replace(/^闰|bis$/g,'').replace(/月$/,''),CM=['正','二','三','四','五','六','七','八','九','十','十一','十二'],lm=/^\d+$/.test(ms)?parseInt(ms,10):CM.indexOf(ms)+1,ld=parseInt((o.day||'').replace(/\D/g,''),10),ry=parseInt(o.relatedYear||o.year,10);if(!lm||!ld)return null;
  var yn=(o.yearName||'').replace(/年$/,'');if(!/^[一-鿿]{2}$/.test(yn))yn=ry>0?'甲乙丙丁戊己庚辛壬癸'[(ry-4)%10]+'子丑寅卯辰巳午未申酉戌亥'[(ry-4)%12]:'';
  return{m:lm,d:ld,leap:/闰|bis/.test(o.month||''),yn:yn}}catch(e){return null}}
function cal(Y,m,d){var N='一二三四五六七八九十',dt=new Date(Y,m-1,d),L=lunar(dt),R=X3.rl||{},out={wk:'星期'+'日一二三四五六'[dt.getDay()],lu:'',yn:'',jq:'',fe:[]};
  if(L){out.lu=(L.leap?'闰':'')+['正','二','三','四','五','六','七','八','九','十','冬','腊'][L.m-1]+'月'+(L.d<=10?'初'+N[L.d-1]:L.d<20?'十'+N[L.d-11]:L.d===20?'二十':L.d<30?'廿'+N[L.d-21]:'三十');
    out.yn=L.yn?L.yn+('鼠牛虎兔龙蛇马羊猴鸡狗猪'['子丑寅卯辰巳午未申酉戌亥'.indexOf(L.yn[1])]||'')+'年':'';
    if(!L.leap){var lk=L.m+'.'+L.d,LF={'1.1':'春节','1.15':'元宵节','5.5':'端午节','7.7':'七夕','8.15':'中秋节','9.9':'重阳节','12.8':'腊八节'};if(LF[lk])out.fe.push(LF[lk]);
      var L2=lunar(new Date(Y,m-1,d+1));if(L2&&L2.m===1&&L2.d===1&&!L2.leap)out.fe.push('除夕')}}
  var GF=HT?{'1.1':'元旦','4.23':'世界讀書日','9.28':'教師節 · 孔子誕辰'}:{'1.1':'元旦','4.23':'世界读书日','5.1':'劳动节','5.4':'青年节','6.1':'儿童节','9.10':'教师节','9.28':'孔子诞辰','10.1':'国庆节'};if(GF[m+'.'+d])out.fe.unshift(GF[m+'.'+d]);
  try{var dd=function(y,i){var s=R.jt[y];return s?s.charCodeAt(i)-48:0},idx=-1,sy=Y,sm,sd;for(var i=23;i>=0;i--){var mo=1+(i>>1),dy=dd(Y,i);if(!dy)break;if(mo<m||(mo===m&&dy<=d)){idx=i;sm=mo;sd=dy;break}}
    if(idx<0&&dd(Y-1,23)){sy=Y-1;idx=23;sm=12;sd=dd(sy,23)}
    if(idx>=0){var k=Math.round((dt-new Date(sy,sm-1,sd))/864e5),h=Math.min(2,Math.floor(k/5));out.jq=(k===0?'今日'+R.jn[idx]:R.jn[idx]+'后第 '+k+' 天')+' · '+R.hou[idx*3+h];if(k===0&&/清明|冬至/.test(R.jn[idx]))out.fe.push(R.jn[idx]+'节')}}catch(e){}
  return out}
function calF(Y,m,d){var dt=new Date(Y,m-1,d),L=lunar(dt),R=X3.rl||{},FE=I.fe||{},out={wk:'',lu:'',yn:[],jq:'',fe:[],dl:''};
  try{out.wk=dt.toLocaleDateString(I.lg,{weekday:'long'});out.dl=dt.toLocaleDateString(I.lg,{year:'numeric',month:'long',day:'numeric',weekday:'long'})}catch(e){}
  if(L){out.lu=(L.leap?I.leap:'')+I.lmd.replace('{m}',L.m).replace('{d}',L.d);var bi=L.yn?'子丑寅卯辰巳午未申酉戌亥'.indexOf(L.yn.charAt(1)):-1;if(L.yn)out.yn=[L.yn].concat(bi>=0&&I.zod?[I.zod[bi]]:[]);
    if(!L.leap){var LF={'1.1':FE.spring,'1.15':FE.lantern,'5.5':FE.duanwu,'7.7':FE.qixi,'8.15':FE.mid,'9.9':FE.chongyang,'12.8':FE.laba};if(LF[L.m+'.'+L.d])out.fe.push(LF[L.m+'.'+L.d]);
      var L2=lunar(new Date(Y,m-1,d+1));if(L2&&L2.m===1&&L2.d===1&&!L2.leap&&FE.eve)out.fe.push(FE.eve)}}
  var GF={'1.1':FE.ny,'4.23':FE.book,'9.28':FE.kz};if(GF[m+'.'+d])out.fe.unshift(GF[m+'.'+d]);
  try{var dd=function(y,i){var s=R.jt[y];return s?s.charCodeAt(i)-48:0},idx=-1,sy=Y,sm,sd;for(var i=23;i>=0;i--){var mo=1+(i>>1),dy=dd(Y,i);if(!dy)break;if(mo<m||(mo===m&&dy<=d)){idx=i;sm=mo;sd=dy;break}}
    if(idx<0&&dd(Y-1,23)){sy=Y-1;idx=23;sm=12;sd=dd(sy,23)}
    if(idx>=0){var k=Math.round((dt-new Date(sy,sm-1,sd))/864e5),h=Math.min(2,Math.floor(k/5));out.jq=(k===0?I.today.replace('{t}',I.jn[idx]):I.after.replace('{t}',I.jn[idx]).replace('{k}',k))+(I.hou&&I.hou.length?' · '+I.hou[idx*3+h]:'')}}catch(e){}
  return out}
function monF(m){try{return new Date(Date.UTC(2026,m-1,15)).toLocaleDateString(I.lg,{month:'long',timeZone:'UTC'})}catch(e){return String(m)}}
function mdF(m,d){try{return new Date(Date.UTC(2026,m-1,d)).toLocaleDateString(I.lg,{month:'long',day:'numeric',timeZone:'UTC'})}catch(e){return m+'/'+d}}
function nlYear(m,d){var t=new Date(),y=t.getFullYear(),td=new Date(y,t.getMonth(),t.getDate());if(y<2027)return 2027;return new Date(y,m-1,d)>=td?y:y+1}
function vtext(c,t,x,y,s){t.split('').forEach(function(ch,i){c.fillText(ch,x,y+i*s*1.18)})}
function nl(){var N=X4.nl;if(!N){yy();return}var R0=RD();if(CN&&!R0.some(function(r){return r.c===CN&&r.d===today()})){R0.push({d:today(),c:CN,n:D.y.replace(/[，。；：？！、“”‘’「」\s]/g,'').length});WR(R0)}var n=N[0],m=N[1],d=N[2],q=hz(N[3])||keyTxt(),bh=ZH?keyBh(keyIdx()):myTr(),days=streak(),Y=nlYear(m,d),K=ZH?cal(Y,m,d):calF(Y,m,d),EV=ZH?'':I.nl_every.replace('{date}',mdF(m,d));
  var T2=function(s){return HT?s.replace(/农历/g,'農曆').replace(/后第/g,'後第').replace(/腊/g,'臘').replace(/闰/g,'閏').replace(/节/g,'節').replace(/马/g,'馬').replace(/鸡/g,'雞').replace(/猪/g,'豬').replace(/龙/g,'龍').replace(/乡/g,'鄉').replace(/动/g,'動').replace(/华/g,'華').replace(/鸟/g,'鳥'):s};
  prep(q+bh+MON[m-1]+'年历第课一年课读完论语每年月日读这一章我读经第天0123456789星期日一二三四五六农历'+K.lu+K.yn+K.jq+K.fe.join('')+T2(K.lu+K.yn+K.jq+K.fe.join(''))+(ZH?'':monF(m)+K.dl+EV+I.nl_h+I.nl_n+I.lunar+I.streak)).then(function(seal){var cv=canvas(),c=cv.getContext('2d');c.fillStyle='#F2F1EA';c.fillRect(0,0,W,H);
    c.fillStyle='#23503F';c.fillRect(0,0,W,250);c.fillStyle='rgba(242,241,234,.85)';[W/2-170,W/2+170].forEach(function(x){c.beginPath();c.arc(x,58,18,0,Math.PI*2);c.fill()});
    c.fillStyle='#F2F1EA';c.textBaseline='alphabetic';c.font='400 26px '+F;c.fillText(ZH?(HT?'《論語》年曆':'《论语》年历'):I.nl_h,84,150);c.textAlign='right';c.fillText(ZH?'第 '+n+' 课 / 365':I.nl_n.replace('{n}',n),W-84,150);c.textAlign='center';c.font='900 64px '+F;c.fillText(ZH?MON[m-1]:monF(m),W/2,212);
    c.strokeStyle='rgba(35,80,63,.35)';c.setLineDash([10,10]);c.lineWidth=2;c.beginPath();c.moveTo(60,262);c.lineTo(W-60,262);c.stroke();c.setLineDash([]);
    c.font='700 64px '+F;var QL=bfit(c,q,W-200,[60,54,48,44,40],230,1.4,700);c.font='400 26px '+F;var BL=bh?(ZH?wrap(c,bh,W-220).slice(0,2):wrapL(c,bh,W-220).slice(0,3)):[],EL=ZH?[]:wrapL(c,EV,W-200);
    var NB=330,hgt=NB+56+(K.fe.length||K.jq?64:0)+50+40+30+QL.L.length*QL.s*1.4+(BL.length?12+BL.length*42:0)+(days>=2?56:0)+(EL.length>1?(EL.length-1)*38:0),y0=262+Math.max(24,((H-212)-262-hgt)/2);
    // 大字日期，左右两条竖排：农历、干支生肖
    c.textAlign='center';c.fillStyle='#A23B2C';c.font='900 340px '+F;c.fillText(String(d),W/2,y0+300);
    if(!ZH){if(K.lu){c.fillStyle='#A23B2C';c.font='700 26px '+F;c.fillText(I.lunar,150,y0+44);c.fillStyle='rgba(162,59,44,.35)';c.fillRect(132,y0+60,36,2);c.fillStyle='#A23B2C';c.font='700 30px '+F;wrapL(c,K.lu,200).slice(0,4).forEach(function(l,i){c.fillText(l,150,y0+112+i*40)})}
      if(K.yn.length){c.fillStyle='#23503F';c.font='700 34px '+F;c.fillText(String(Y),W-150,y0+44);c.fillStyle='rgba(35,80,63,.35)';c.fillRect(W-168,y0+60,36,2);c.fillStyle='#23503F';c.font='400 36px '+F;c.fillText(K.yn[0],W-150,y0+112);c.font='400 26px '+F;(K.yn[1]?wrapL(c,K.yn[1],200):[]).slice(0,3).forEach(function(l,i){c.fillText(l,W-150,y0+156+i*36)})}}
    else{
    if(K.lu){c.fillStyle='#A23B2C';c.font='700 34px '+F;c.fillText(HT?'農曆':'农历',150,y0+44);c.fillStyle='rgba(162,59,44,.35)';c.fillRect(132,y0+60,36,2);c.fillStyle='#A23B2C';c.font='700 46px '+F;vtext(c,T2(K.lu),150,y0+120,46)}
    if(K.yn){c.fillStyle='#23503F';c.font='700 34px '+F;c.fillText(String(Y),W-150,y0+44);c.fillStyle='rgba(35,80,63,.35)';c.fillRect(W-168,y0+60,36,2);c.fillStyle='#23503F';c.font='400 36px '+F;vtext(c,T2(K.yn),W-150,y0+112,36)}}
    var y=y0+NB+44;c.fillStyle='#23503F';c.font='700 32px '+F;c.fillText(ZH?Y+' 年 '+m+' 月 '+d+' 日 · '+K.wk:K.dl,W/2,y);
    // 节日、节气做成小签
    var tags=K.fe.map(function(f){return [T2(f),1]}).concat(K.jq?[[T2(K.jq),0]]:[]);if(tags.length){y+=26;c.font='400 25px '+F;var tw=tags.map(function(t){return c.measureText(t[0]).width+44}),sum=tw.reduce(function(a,b){return a+b},0)+(tags.length-1)*16,tx=W/2-sum/2;
      tags.forEach(function(t,i){c.fillStyle=t[1]?'#A23B2C':'rgba(35,80,63,.1)';rr(c,tx,y,tw[i],44,22);c.fill();c.fillStyle=t[1]?'#FFFFFF':'#23503F';c.font=(t[1]?'700':'400')+' 25px '+F;c.fillText(t[0],tx+tw[i]/2,y+31);tx+=tw[i]+16});y+=44}
    y+=50;c.fillStyle='#8A5A2C';c.font='400 26px '+F;if(ZH)c.fillText('每年 '+m+' 月 '+d+' 日读这一章 · 一年 365 课读完《论语》',W/2,y);else EL.forEach(function(l,i){if(i)y+=38;c.fillText(l,W/2,y)});
    y+=30;c.fillStyle='#23503F';c.fillRect(W/2-32,y,64,4);y+=30;c.fillStyle='#1a1a1a';c.font='700 '+QL.s+'px '+F;
    QL.L.forEach(function(l){c.fillText(l,W/2,y+QL.s);y+=QL.s*1.4});
    if(BL.length){y+=12;c.fillStyle='#666';c.font='400 26px '+F;BL.forEach(function(l){c.fillText(l,W/2,y+26);y+=42})}
    if(days>=2){c.fillStyle='#23503F';c.font='700 26px '+F;c.fillText(ZH?'我读经第 '+days+' 天':I.streak.replace('{n}',days),W/2,y+44)}c.textAlign='left';
    foot4(c,seal,false,'nl');show(cv)})}
TABS=[['yy','原页卡'],['rw','人物卡'],['dy','多语卡'],['nl','年历卡']].map(function(t,i){return ZH||!I.tabs?t:[t[0],I.tabs[i]]}).filter(function(t){return (t[0]!=='rw'||(X4.who||[]).length)&&(t[0]!=='nl'||X4.nl)});
var show0=show;show=function(cv){show0(cv);var M=document.querySelectorAll('.shmodal'),m=M[M.length-1];if(!m)return;var box=m.querySelector('.shm'),bar=document.createElement('div');bar.className='shtabs';
  TABS.forEach(function(t){var b=document.createElement('button');b.type='button';b.textContent=t[1];if(t[0]===KIND)b.className='on';b.onclick=function(){m.remove();if(t[0]==='bing')window.ykBing();else pick(t[0])};bar.appendChild(b)});box.insertBefore(bar,box.firstChild);
  if(KIND==='he'&&HT){var vb=document.createElement('div');vb.className='shtabs shvt';[['0','橫排'],['1','直排']].forEach(function(o){var b=document.createElement('button');b.type='button';b.textContent=o[1];if((VT?'1':'0')===o[0])b.className='on';b.onclick=function(){VT=o[0]==='1';try{localStorage.setItem('yk_vt',VT?'1':'0')}catch(e){}m.remove();he()};vb.appendChild(b)});box.insertBefore(vb,bar.nextSibling)}
  if(KIND==='bing'||KIND==='nl'){var nt=document.createElement('p');nt.className='note shrec';nt.textContent=ZH?'读过的章记在这台设备上。换手机或电脑时，先导出一串记录码，到新设备上粘进去恢复。':I.rec_note;var bx=document.createElement('div');bx.className='shmb';
    var ex=document.createElement('button');ex.type='button';ex.className='btn ghost';ex.textContent=ZH?'导出记录':I.rec_ex;ex.onclick=function(){var code='YK1.'+btoa(unescape(encodeURIComponent(JSON.stringify(RD().map(function(r){return[r.d,r.c,r.n||0]})))));
      if(navigator.clipboard)navigator.clipboard.writeText(code).then(function(){ex.textContent=ZH?'已复制记录码':I.rec_copied},function(){prompt(ZH?'记录码':I.rec_code,code)});else prompt(ZH?'记录码':I.rec_code,code)};
    var im=document.createElement('button');im.type='button';im.className='btn ghost';im.textContent=ZH?'恢复记录':I.rec_im;im.onclick=function(){var s=prompt(ZH?'粘贴记录码':I.rec_paste);if(!s)return;try{var a=JSON.parse(decodeURIComponent(escape(atob(s.trim().replace(/^YK1\./,''))))),cur=RD(),seen={};cur.forEach(function(r){seen[r.d+'|'+r.c]=1});
      a.forEach(function(x){if(!seen[x[0]+'|'+x[1]])cur.push({d:x[0],c:x[1],n:x[2]})});cur.sort(function(p,q){return p.d<q.d?-1:1});WR(cur);m.remove();pick(ZH?'bing':'nl')}catch(e){alert(ZH?'记录码不对':I.rec_bad)}};
    bx.appendChild(ex);bx.appendChild(im);box.appendChild(nt);box.appendChild(bx)}};
function pick(k){KIND=k;if(k==='yy')yy();else if(k==='rw')rw();else if(k==='dy')dy();else if(k==='nl')nl();else if(k==='he')he();else if(k==='bing')bing();else card()}
window.ykPick=pick;
if(ZH)window.ykBing=function(){var R=RD(),td=today();if(CN&&!R.some(function(r){return r.c===CN})){R.push({d:td,c:CN,n:D.y.replace(/[，。；：？！、“”‘’「」\s]/g,'').length});WR(R)}pick('bing')};
})()}
