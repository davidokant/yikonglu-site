/* 手机访客“加到桌面”提示：第二次来访或看满三页才出；可关，关后 30 天不出；已从桌面打开的不出；电脑不出。 */
(function(){
var LS={g:function(k){try{return localStorage.getItem(k)}catch(e){return null}},s:function(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
var ua=navigator.userAgent||"",now=Date.now(),DAY=864e5;
var ios=/iPhone|iPad|iPod/.test(ua)||(/Macintosh/.test(ua)&&navigator.maxTouchPoints>1),and=/Android/.test(ua);
var standalone=(window.matchMedia&&matchMedia("(display-mode: standalone)").matches)||navigator.standalone===true;
if(standalone){LS.s("yk_a2hs_inst","1");return}
if(!ios&&!and)return;
var pv=+(LS.g("yk_pv")||0)+1,last=+(LS.g("yk_last")||0),vis=+(LS.g("yk_vis")||0);
if(now-last>18e5)vis++;LS.s("yk_pv",pv);LS.s("yk_vis",vis);LS.s("yk_last",now);
if(LS.g("yk_a2hs_inst")||now-(+(LS.g("yk_a2hs_off")||0))<30*DAY)return;
var T={
"zh-Hans":{h:"把一孔录加到桌面",p:"下次一点就开，像 App 一样，看过的章节离线也能读。",go:"加到桌面",how:"怎么加",s0:"点地址栏旁的“···”菜单按钮",s1:"点“共享”",s2:"选“添加到主屏幕”（没看到就往下滑）",s1b:"旧版 Safari 底栏直接有共享按钮，可跳过第一步",man:"在浏览器菜单（⋮ 或 ≡）里选“添加到桌面”或“添加到主屏幕”。",wx:"微信里加不了：点右上角 ··· ，选用浏览器打开，再加到桌面。",x:"关闭"},
"zh-Hant":{h:"把一孔錄加到主畫面",p:"下次一點就開，像 App 一樣，看過的章節離線也能讀。",go:"加到主畫面",how:"怎麼加",s0:"點網址列旁的「···」選單按鈕",s1:"點「分享」",s2:"選「加入主畫面」（沒看到就往下滑）",s1b:"舊版 Safari 底欄直接有分享按鈕，可略過第一步",man:"在瀏覽器選單（⋮ 或 ≡）裡選「加到主畫面」。",wx:"微信裡加不了：點右上角 ··· ，選用瀏覽器開啟，再加到主畫面。",x:"關閉"},
"en":{h:"Add Yikonglu to your home screen",p:"Open it in one tap like an app; chapters you have read work offline.",go:"Add",how:"How",s0:"Tap the “···” menu button by the address bar",s1:"Tap “Share”",s2:"Choose “Add to Home Screen” (scroll down if needed)",s1b:"Older Safari shows Share in the bottom bar; skip step 1",man:"In the browser menu (⋮ or ≡), choose “Add to Home screen” or “Install app”.",wx:"This can't be done inside WeChat: tap ··· at the top right and open in your browser, then add it.",x:"Close"},
"ja":{h:"一孔録をホーム画面に追加",p:"次からワンタップでアプリのように開けます。読んだ章はオフラインでも読めます。",go:"追加",how:"方法",s0:"アドレスバー横の「···」メニューをタップ",s1:"「共有」をタップ",s2:"「ホーム画面に追加」を選ぶ（なければ下へスクロール）",s1b:"旧版 Safari は下部に共有ボタンがあるので手順1は不要",man:"ブラウザのメニュー（⋮ または ≡）から「ホーム画面に追加」を選んでください。",wx:"WeChat 内では追加できません。右上の ··· からブラウザで開いてから追加してください。",x:"閉じる"},
"ko":{h:"일공록을 홈 화면에 추가",p:"다음부터 앱처럼 한 번에 열립니다. 읽은 장은 오프라인에서도 볼 수 있습니다.",go:"추가",how:"방법",s0:"주소창 옆 “···” 메뉴 버튼을 누르세요",s1:"“공유”를 누르세요",s2:"“홈 화면에 추가”를 선택 (안 보이면 아래로 스크롤)",s1b:"이전 Safari는 하단에 공유 버튼이 있어 1단계를 건너뜁니다",man:"브라우저 메뉴(⋮ 또는 ≡)에서 “홈 화면에 추가”를 선택하세요.",wx:"WeChat 안에서는 추가할 수 없습니다. 오른쪽 위 ··· 에서 브라우저로 연 뒤 추가하세요.",x:"닫기"},
"fr":{h:"Ajouter Yikonglu à l'écran d'accueil",p:"Ouvrez-le d'un geste, comme une appli ; les chapitres lus restent disponibles hors ligne.",go:"Ajouter",how:"Comment",s0:"Touchez le bouton menu « ··· » près de la barre d’adresse",s1:"Touchez « Partager »",s2:"Choisissez « Sur l’écran d’accueil » (faites défiler si besoin)",s1b:"Sur un Safari plus ancien, Partager est dans la barre du bas : passez l’étape 1",man:"Dans le menu du navigateur (⋮ ou ≡), choisissez « Ajouter à l'écran d'accueil ».",wx:"Impossible dans WeChat : touchez ··· en haut à droite, ouvrez dans le navigateur, puis ajoutez.",x:"Fermer"},
"es":{h:"Añade Yikonglu a tu pantalla de inicio",p:"Ábrelo con un toque, como una app; los capítulos leídos funcionan sin conexión.",go:"Añadir",how:"Cómo",s0:"Toca el botón de menú «···» junto a la barra de direcciones",s1:"Toca «Compartir»",s2:"Elige «Añadir a pantalla de inicio» (desliza si no aparece)",s1b:"En Safari antiguo, Compartir está en la barra inferior: omite el paso 1",man:"En el menú del navegador (⋮ o ≡), elige «Añadir a pantalla de inicio».",wx:"No se puede dentro de WeChat: toca ··· arriba a la derecha, abre en el navegador y añádelo.",x:"Cerrar"}};
var t=T[document.documentElement.lang]||T["zh-Hans"];
var inapp=/MicroMessenger|QQ\/|Weibo|aweme|NewsArticle|DingTalk|Lark/i.test(ua);
var pureChrome=/Chrome\/[\d.]+ Mobile Safari\/[\d.]+$/.test(ua);
var SH='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 3v12M8 7l4-4 4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 11H5v10h14V11h-1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>';
var PL='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
var DT='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="7.5" cy="12" r="1.4" fill="currentColor"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/><circle cx="16.5" cy="12" r="1.4" fill="currentColor"/></svg>';
var ev=null,bar=null;
function off(){LS.s("yk_a2hs_off",Date.now());if(bar)bar.remove()}
function show(kind){
  if(bar||!(pv>=3||vis>=2))return;
  bar=document.createElement("div");bar.className="a2hs";bar.setAttribute("role","dialog");
  var act=kind==="prompt"?'<button class="a2go">'+t.go+'</button>':kind==="ios"?'<button class="a2go">'+t.how+'</button>':"";
  var msg=kind==="inapp"?t.wx:kind==="manual"?t.man:t.p;
  bar.innerHTML='<img src="/assets/seal-180.png" alt="" width="40" height="40"><div class="a2t"><b>'+t.h+'</b><span>'+msg+'</span>'+
    (kind==="ios"?'<ol class="a2steps" hidden><li><i>'+DT+'</i><span>'+t.s0+'</span></li><li><i>'+SH+'</i><span>'+t.s1+'</span></li><li><i>'+PL+'</i><span>'+t.s2+'</span></li><li class="a2n">'+t.s1b+'</li></ol>':"")+'</div>'+act+'<button class="a2x" aria-label="'+t.x+'">×</button>';
  bar.querySelector(".a2x").onclick=off;
  var g=bar.querySelector(".a2go");
  if(g)g.onclick=function(){
    if(kind==="prompt"&&ev){ev.prompt();ev.userChoice.then(function(r){if(r&&r.outcome==="accepted")LS.s("yk_a2hs_inst","1");bar.remove()});ev=null}
    else{bar.querySelector(".a2steps").hidden=false;g.remove()}};
  document.body.appendChild(bar);
}
addEventListener("appinstalled",function(){LS.s("yk_a2hs_inst","1");if(bar)bar.remove()});
if(inapp){setTimeout(function(){show("inapp")},1500);return}
if(ios){setTimeout(function(){show("ios")},1500);return}
addEventListener("beforeinstallprompt",function(e){e.preventDefault();ev=e;setTimeout(function(){show("prompt")},800)});
if(!pureChrome)setTimeout(function(){if(!ev)show("manual")},4000);
})();
