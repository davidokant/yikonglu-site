(function(){var D=function(){return document.querySelectorAll('details.lang[open]')};
document.addEventListener('click',function(e){D().forEach(function(d){if(!d.contains(e.target))d.removeAttribute('open')})});
document.addEventListener('keydown',function(e){if(e.key==='Escape')D().forEach(function(d){d.removeAttribute('open')})});
document.querySelectorAll('details.lang').forEach(function(d){d.addEventListener('toggle',function(){if(d.open)D().forEach(function(x){if(x!==d)x.removeAttribute('open')})})})})();
(function(){var P=document.documentElement.lang,K='yk_lang';try{var s=localStorage.getItem(K)}catch(e){var s=null}
document.querySelectorAll('[data-lang]').forEach(function(a){a.addEventListener('click',function(){try{localStorage.setItem(K,a.dataset.lang)}catch(e){}})});
if(s)return;var n=(navigator.language||'').toLowerCase(),w=null;
var c2=n.slice(0,2);if(c2=='in')c2='id';if(['en','ja','ko','fr','es','de','vi','id','ru'].indexOf(c2)>=0)w=c2;else if(n.startsWith('zh')&&/tw|hk|mo|hant/.test(n))w='zh-Hant';else if(n.startsWith('zh'))w='zh-Hans';
if(!w||w===P)return;var a=document.querySelector('link[hreflang="'+w+'"]');if(!a)return;
var t={en:['This page is available in English.','Switch to English'],ja:['このページには日本語版があります。','日本語に切り替える'],ko:['이 페이지는 한국어판이 있습니다.','한국어로 전환'],fr:['Cette page existe en français.','Passer au français'],es:['Esta página está disponible en español.','Cambiar a español'],de:['Diese Seite gibt es auf Deutsch.','Auf Deutsch lesen'],vi:['Trang này có bản tiếng Việt.','Chuyển sang tiếng Việt'],id:['Halaman ini tersedia dalam bahasa Indonesia.','Baca dalam bahasa Indonesia'],ru:['Эта страница есть на русском.','Читать по-русски'],'zh-Hant':['本頁有繁體中文版。','切換到繁體'],'zh-Hans':['本页有简体中文版。','切换到简体']}[w];
var b=document.createElement('div');b.className='langbar';b.innerHTML='<span>'+t[0]+'</span><a href="'+a.href+'">'+t[1]+' →</a><button aria-label="close">×</button>';
b.querySelector('a').onclick=function(){try{localStorage.setItem(K,w)}catch(e){}};b.querySelector('button').onclick=function(){try{localStorage.setItem(K,P)}catch(e){}b.remove()};
document.body.prepend(b)})();
