(function(){var B=document.getElementById('jubar'),Q=document.querySelector('.yuanwen blockquote'),cur=null;if(!Q)return;
function put(t,btn){var done=function(){var o=btn.textContent;btn.textContent='Скопировано';setTimeout(function(){btn.textContent=o;B.hidden=true},1200)};
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,function(){prompt('',t)})}else{prompt('',t)}}
function show(s){cur=s;document.querySelectorAll('.ju.on').forEach(function(x){x.classList.remove('on')});s.classList.add('on');
var J=B.querySelector('.jr'),R=[];try{R=JSON.parse(Q.dataset.reads||'[]')}catch(e){}
var t=s.textContent,hit=R.filter(function(x){return x[1].split('、').some(function(p){return p&&t.indexOf(p)>=0})});
J.hidden=!hit.length;J.textContent=hit.length?Q.dataset.rl+hit.map(function(x){return x[0]+' '+x[2]}).join(' · '):'';
var U=B.querySelector('.hjd'),H=[];try{H=JSON.parse(Q.dataset.hj||'{}')[s.id.slice(1)]||[]}catch(e){}
U.innerHTML='';H.forEach(function(x){var li=document.createElement('li');li.innerHTML='<i></i> ';li.firstChild.textContent=x[0];var a=document.createElement(x[3]?'a':'span');a.textContent=x[1]+(x[2]?'（'+x[2]+'）':'');if(x[3])a.href=x[3];li.appendChild(a);U.appendChild(li)});
var r=s.getBoundingClientRect();B.hidden=false;B.style.top=(window.scrollY+r.bottom+6)+'px';B.style.left=Math.max(8,Math.min(window.scrollX+r.left,document.documentElement.clientWidth-B.offsetWidth-8))+'px'}
Q.addEventListener('click',function(e){var s=e.target.closest('.ju');if(s)show(s)});
Q.addEventListener('keydown',function(e){if(e.key==='Enter'){var s=e.target.closest('.ju');if(s)show(s)}});
document.addEventListener('click',function(e){var c=e.target.closest('.cp');if(c){put(c.dataset.t,c);return}if(!e.target.closest('.ju')&&!e.target.closest('#jubar')){B.hidden=true;if(cur)cur.classList.remove('on')}});
B.addEventListener('click',function(e){var b=e.target.closest('button');if(!b||!cur)return;var u=Q.dataset.url+'#'+cur.id;
put(b.dataset.a==='q'?'“'+cur.textContent+'”——'+Q.dataset.src+(Q.dataset.short?' '+Q.dataset.short:Q.dataset.sep+u):u,b);if(window.yklCopy)window.yklCopy(cur.id)});
var h=location.hash.slice(1);if(/^s\d+$/.test(h)){var t=document.getElementById(h);if(t)t.classList.add('on')}})();
