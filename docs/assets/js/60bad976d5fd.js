(function(){var D=JSON.parse(document.getElementById('zidata').textContent),P=document.getElementById('zipop'),cur=null;
function off(){P.hidden=true;if(cur)cur.classList.remove('on');cur=null}
function show(z){var it=D.i[z.dataset.o];if(!it)return;if(cur)cur.classList.remove('on');cur=z;z.classList.add('on');
P.querySelector('.zz').textContent=it[0];P.querySelector('.zp').textContent=it[1];
var g=P.querySelector('.zg');g.textContent='';if(it[2]){g.appendChild(document.createTextNode(it[2]));var s=document.createElement('small');s.textContent='（'+it[3]+'）';g.appendChild(s)}g.hidden=!it[2];
var o=P.querySelector('.zo'),L=D.o[it[0]+'|'+it[1]]||[];o.textContent='全書讀 '+it[1]+' 的「'+it[0]+'」共 '+L.length+' 章：';
L.forEach(function(x,i){if(i)o.appendChild(document.createTextNode(' '));var a=document.createElement(x[0]===D.c?'b':'a');a.textContent=x[0];if(x[0]!==D.c)a.href=x[1];o.appendChild(a)});var U=D.u&&D.u[it[0]+'|'+it[1]];if(U){var ua=document.createElement('a');ua.className='zil';ua.href=U;ua.textContent='這個字的專頁 ›';o.appendChild(document.createElement('br'));o.appendChild(ua)}
var r=z.getBoundingClientRect();P.hidden=false;P.style.top=(window.scrollY+r.bottom+6)+'px';P.style.left=Math.max(8,Math.min(window.scrollX+r.left-12,document.documentElement.clientWidth-P.offsetWidth-8))+'px';var pr=P.getBoundingClientRect();if(pr.bottom>innerHeight)window.scrollBy({top:pr.bottom-innerHeight+12,behavior:'smooth'})}
document.addEventListener('click',function(e){var z=e.target.closest&&e.target.closest('.nz');if(z){e.stopPropagation();e.preventDefault();if(cur===z)off();else show(z);return}
if(!P.hidden&&!P.contains(e.target))off();else if(e.target.closest&&e.target.closest('.zx'))off()},true);
document.addEventListener('keydown',function(e){if(e.key==='Escape')off()})})();
