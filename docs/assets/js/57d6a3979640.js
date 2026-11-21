(function(){var F=document.querySelector('.yuanwen.dz');if(!F)return;var Q=F.querySelector('blockquote'),C=document.getElementById('zjcard'),S=[];try{S=JSON.parse(F.querySelector('.zjdata').textContent)}catch(e){}
var TABS=[["bh", "白話"], ["zhu", "朱注"], ["jj", "集解"], ["yk", "一孔讀法"], ["hj", "本句互見"]],cur=null,sel='',tab='bh';
function hl(n){F.querySelectorAll('.yyp .hl').forEach(function(r){r.classList.toggle('on',r.dataset.s==n)});var r=F.querySelector('.yyp .hl[data-s="'+n+'"]'),P=F.querySelector('.yypane');if(r&&P&&P.scrollHeight>P.clientHeight+4){var a=r.getBoundingClientRect(),b=P.getBoundingClientRect();P.scrollTo({top:P.scrollTop+a.top-b.top-(b.height-a.height)/2,left:P.scrollLeft+a.left-b.left-(b.width-a.width)/2,behavior:'smooth'})}else if(r){var q=r.getBoundingClientRect();if(q.top<0||q.bottom>innerHeight)r.scrollIntoView({block:'nearest',behavior:'smooth'})}}
function esc(t){var d=document.createElement('div');d.textContent=t;return d.innerHTML}
function body(){var d=S[cur.dataset.n-1]||{},B=C.querySelector('.zb'),v=d[tab];C.querySelectorAll('.zt button').forEach(function(b){b.classList.toggle('on',b.dataset.t===tab)});
if(!v||!v.length){B.innerHTML='<p><small>這一句沒有收。</small></p>';return}
if(typeof v==='string'){B.innerHTML='<p>'+esc(v)+'</p>';return}
B.innerHTML=v.map(function(x){return '<p>'+esc(x[0])+(x[1]?'<small>'+esc(x[1])+'</small>':'')+(x[2]?'<small class="dai">'+esc(x[2])+'</small>':'')+'</p>'}).join('')}
function open(s,txt){cur=s;sel=txt||'';F.querySelectorAll('.ju.on').forEach(function(x){x.classList.remove('on')});s.classList.add('on');hl(s.dataset.n);
C.querySelector('.zq').textContent=sel||s.textContent;var d=S[s.dataset.n-1]||{};
C.querySelector('.zt').innerHTML=TABS.filter(function(t){return d[t[0]]&&d[t[0]].length}).map(function(t){return '<button type="button" data-t="'+t[0]+'">'+t[1]+'</button>'}).join('');
if(!(d[tab]&&d[tab].length)){var f0=TABS.filter(function(t){return d[t[0]]&&d[t[0]].length})[0];tab=f0?f0[0]:'bh'}body();
var R=[];try{R=JSON.parse(Q.dataset.reads||'[]')}catch(e){}var t=s.textContent,hit=R.filter(function(x){return x[1].split('\u3001').some(function(p){return p&&t.indexOf(p)>=0})});
C.querySelector('.zx').textContent=hit.length?Q.dataset.rl+hit.map(function(x){return x[0]+' '+x[2]}).join(' \u00b7 '):'';
var r=(window.getSelection&&sel&&getSelection().rangeCount?getSelection().getRangeAt(0):s).getBoundingClientRect();C.hidden=false;C.style.top=(window.scrollY+r.bottom+8)+'px';C.style.left=Math.max(8,Math.min(window.scrollX+r.left,document.documentElement.clientWidth-C.offsetWidth-8))+'px';
var N=F.querySelectorAll('.ju[data-n]').length,k=+s.dataset.n;C.querySelector('[data-a=pv]').disabled=k<=1;C.querySelector('[data-a=nx]').disabled=k>=N;
try{history.replaceState(null,'','#'+s.id)}catch(e){}}
function step(d){if(!cur)return;var s=F.querySelector('.ju[data-n="'+(+cur.dataset.n+d)+'"]');if(s){open(s);var r=s.getBoundingClientRect();if(r.top<60||r.bottom>innerHeight-40)s.scrollIntoView({block:'center',behavior:'smooth'})}}
function close(){C.hidden=true;if(cur)cur.classList.remove('on');cur=null}
function cite(t,s){return '\u201c'+t+'\u201d\u2014\u2014'+Q.dataset.src+(Q.dataset.short?' '+Q.dataset.short:Q.dataset.sep+Q.dataset.url+'#'+s.id)}
function put(t,b){var o=b.textContent,done=function(){b.textContent='已複製';setTimeout(function(){b.textContent=o},1200)};if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(done,function(){prompt('',t)});else prompt('',t)}
Q.addEventListener('click',function(e){var s=e.target.closest('.ju');if(!s)return;var g=window.getSelection?String(getSelection()).trim():'';if(g&&s.contains(getSelection().anchorNode))open(s,g.replace(/\s+/g,''));else open(s)});
Q.addEventListener('keydown',function(e){if(e.key==='Enter'){var s=e.target.closest('.ju');if(s)open(s)}});
document.addEventListener('selectionchange',function(){var g=getSelection();if(!g.rangeCount||g.isCollapsed)return;var n=g.anchorNode&&(g.anchorNode.nodeType===1?g.anchorNode:g.anchorNode.parentNode),s=n&&n.closest&&n.closest('.ju');if(s&&Q.contains(s)){clearTimeout(window._zjt);window._zjt=setTimeout(function(){var t=String(getSelection()).trim().replace(/\s+/g,'');if(t)open(s,t)},450)}});
C.addEventListener('click',function(e){var b=e.target.closest('button');if(!b||!cur)return;if(b.dataset.t){tab=b.dataset.t;body();return}
var a=b.dataset.a;if(a==='pv'||a==='nx'){step(a==='pv'?-1:1);return}if(a==='q'){put(cite(sel||cur.textContent,cur),b);if(window.yklCopy)window.yklCopy(cur.id)}else if(a==='l')put(Q.dataset.url+'#'+cur.id,b);else if(a==='img'){if(window.ykPickSent)window.ykPickSent(+cur.dataset.n);else if(window.yklCard)window.yklCard({y:sel||cur.textContent,u:Q.dataset.url+'#'+cur.id,n:cur.dataset.n})}});
document.addEventListener('click',function(e){if(!C.hidden&&!C.contains(e.target)&&!e.target.closest('.ju')&&!e.target.closest('.dztools'))close()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')close();else if(!C.hidden&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){e.preventDefault();step(e.key==='ArrowLeft'?-1:1)}});
var tx=null;C.addEventListener('touchstart',function(e){tx=e.touches[0].clientX},{passive:true});C.addEventListener('touchend',function(e){if(tx===null)return;var dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>50)step(dx<0?1:-1)},{passive:true});
var TP=document.querySelector('.top');function th(){if(TP)document.documentElement.style.setProperty('--toph',TP.offsetHeight+'px')}th();addEventListener('resize',th);
Q.addEventListener('copy',function(e){var g=getSelection(),t=String(g).replace(/\s+/g,'');if(!t||!e.clipboardData)return;var n=g.anchorNode&&(g.anchorNode.nodeType===1?g.anchorNode:g.anchorNode.parentNode),s=n&&n.closest&&n.closest('.ju')||Q.querySelector('.ju');e.clipboardData.setData('text/plain',cite(t,s));e.preventDefault()});
var Y=F.querySelector('.yibtn'),YK='yk_yi';function yi(on){Y.setAttribute('aria-pressed',on?'true':'false');F.classList.toggle('yion',on);F.querySelectorAll('.yi').forEach(function(x){x.hidden=!on});try{localStorage.setItem(YK,on?'1':'0')}catch(e){}}
if(Y){var on0=false;try{on0=localStorage.getItem(YK)==='1'}catch(e){}yi(on0);Y.addEventListener('click',function(){yi(Y.getAttribute('aria-pressed')!=='true')})}
var h=location.hash.slice(1);if(/^s\d+$/.test(h)){var t=document.getElementById(h);if(t&&Q.contains(t)){t.classList.add('on');setTimeout(function(){hl(t.dataset.n)},300)}}
})();
