(function(){var q=new URLSearchParams(location.search),f=(q.get('from')||'').toLowerCase();if(!f)return;
var V={yt:'YouTube',bili:'嗶哩嗶哩',dy:'抖音',ks:'快手',sph:'影片號'},T={xhs:'小紅書',pod:'播客',gzh:'公眾號',zhihu:'知乎',bjh:'百家號',tt:'頭條'},nm=V[f]||T[f];
try{q.delete('from');history.replaceState(null,'',location.pathname+(q.toString()?'?'+q:'')+location.hash)}catch(e){}
if(!nm)return;try{if(sessionStorage.getItem('yk_from'))return;sessionStorage.setItem('yk_from',f)}catch(e){}
var H=document.querySelector('.chhead .wrap');if(!H)return;var d=document.createElement('p');d.className='fromtip';var m,go=null;
if(V[f]){m='從'+nm+'過來的？片裡講的原文都在下面，點任何一句，原頁上那幾列就框出來；朱注和各家說法在“細讀與核對”。'}
else if(f==='xhs'){m='從小紅書過來的？這一章可以一鍵做成帶原文底紋的分享圖，存下來就能發。';go=['生成分享圖',function(){var p=document.querySelector('.shpanel');if(!p)return;if(p.hidden)p.previousElementSibling.click();var b=p.querySelector('[data-p=card]');if(b)b.click()}]}
else if(f==='pod'){m='從播客過來的？按原文上方的“音”，可以邊聽原文朗讀邊看原頁。';go=['聽原文',function(){var b=document.querySelector('.ldbtn');if(b){b.scrollIntoView({block:'center',behavior:'smooth'});b.click()}}]}
else{m='從'+nm+'過來的？這裡有原文、原頁和一孔之見，每條引文都標了底本頁碼，點句就能核。'}
d.textContent=m;if(go){var a=document.createElement('button');a.type='button';a.textContent=go[0];a.onclick=go[1];d.appendChild(a)}
var x=document.createElement('button');x.type='button';x.className='fx';x.setAttribute('aria-label','關閉');x.textContent='×';x.onclick=function(){d.remove()};d.appendChild(x);H.appendChild(d)})();
