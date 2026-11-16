(function(){var q=new URLSearchParams(location.search),f=(q.get('from')||'').toLowerCase();if(!f)return;
var V={yt:'YouTube',bili:'哔哩哔哩',dy:'抖音',ks:'快手',sph:'视频号'},T={xhs:'小红书',pod:'播客',gzh:'公众号',zhihu:'知乎',bjh:'百家号',tt:'头条'},nm=V[f]||T[f];
try{q.delete('from');history.replaceState(null,'',location.pathname+(q.toString()?'?'+q:'')+location.hash)}catch(e){}
if(!nm)return;try{if(sessionStorage.getItem('yk_from'))return;sessionStorage.setItem('yk_from',f)}catch(e){}
var H=document.querySelector('.chhead .wrap');if(!H)return;var d=document.createElement('p');d.className='fromtip';var m,go=null;
if(V[f]){m='从'+nm+'过来的？片里讲的原文都在下面，点任何一句，原页上那几列就框出来；朱注和各家说法在“细读与核对”。'}
else if(f==='xhs'){m='从小红书过来的？这一章可以一键做成带原文底纹的分享图，存下来就能发。';go=['生成分享图',function(){var p=document.querySelector('.shpanel');if(!p)return;if(p.hidden)p.previousElementSibling.click();var b=p.querySelector('[data-p=card]');if(b)b.click()}]}
else if(f==='pod'){m='从播客过来的？按原文上方的“音”，可以边听原文朗读边看原页。';go=['听原文',function(){var b=document.querySelector('.ldbtn');if(b){b.scrollIntoView({block:'center',behavior:'smooth'});b.click()}}]}
else{m='从'+nm+'过来的？这里有原文、原页和一孔之见，每条引文都标了底本页码，点句就能核。'}
d.textContent=m;if(go){var a=document.createElement('button');a.type='button';a.textContent=go[0];a.onclick=go[1];d.appendChild(a)}
var x=document.createElement('button');x.type='button';x.className='fx';x.setAttribute('aria-label','关闭');x.textContent='×';x.onclick=function(){d.remove()};d.appendChild(x);H.appendChild(d)})();
