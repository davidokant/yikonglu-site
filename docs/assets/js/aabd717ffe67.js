(function(){var T={"st": "{a} 関点灯 · {b} 関突破 · うち {c} 章読了", "nx": "次の関", "ok": "突破", "go": "続きから：", "all": "この関は突破済み。もう一度読むのも温故です。", "rd": "{x} / {n} 章読了", "st0": "第一関から"};
var seen=[];try{seen=((JSON.parse(localStorage.getItem("yk_xd")||"{}").b||{}).lunyu||{}).seen||[]}catch(e){}
var S={};seen.forEach(function(c){S[c]=1});function cs(el){try{return JSON.parse(el.getAttribute("data-cs"))}catch(e){return[]}}
function f(t,o){return t.replace(/\{(\w+)\}/g,function(_,k){return o[k]})}
var a=0,b=0,u={},nx=null;document.querySelectorAll(".qn").forEach(function(li){var C=cs(li),x=C.filter(function(c){return S[c]}).length,p=C.length?x/C.length:0;
 li.style.setProperty("--p",(p*100).toFixed(1)+"%");if(x){li.classList.add("lit");a++;C.forEach(function(c){if(S[c])u[c]=1})}if(x&&x==C.length){li.classList.add("done");b++}else if(!nx)nx=li;
 var q=li.querySelector(".qc");if(q&&x)q.textContent=x+" / "+C.length});
if(nx){nx.classList.add("next");var tg=document.createElement("em");tg.className="qtag";tg.textContent=T.nx;nx.querySelector("a").appendChild(tg)}
var st=document.getElementById("qstat");if(st&&a)st.textContent=f(T.st,{a:a,b:b,c:Object.keys(u).length});
document.querySelectorAll(".qbar").forEach(function(qb){var C=cs(qb),x=C.filter(function(c){return S[c]}).length,n=C.length;qb.querySelector(".bar i").style.width=(n?x*100/n:0)+"%";
 if(x)qb.classList.add("lit");if(x==n&&n)qb.classList.add("done");var s=qb.querySelector(".qbs");if(x&&s)s.textContent=f(T.rd,{x:x,n:n})+(x==n?" · "+T.ok:"");
 var g=qb.querySelector(".qgo"),c0=null;document.querySelectorAll(".ztl li[data-c]").forEach(function(li){var c=li.getAttribute("data-c");if(S[c])li.classList.add("rd");else if(!c0&&!li.classList.contains("wj"))c0=li});
 if(!c0)c0=[].filter.call(document.querySelectorAll(".ztl li[data-c]"),function(li){return !S[li.getAttribute("data-c")]})[0];
 if(c0){var A=c0.querySelector("a");g.innerHTML='<a class="btn" href="'+A.getAttribute("href")+'">'+T.go+A.querySelector("em").textContent+" "+A.querySelector("b").textContent+" →</a>"}else g.textContent=T.all});
document.querySelectorAll(".gsroute[data-cs]").forEach(function(r){var C=cs(r),x=C.filter(function(c){return S[c]}).length;if(!x)return;var d=r.querySelector("div"),e=document.createElement("small");e.className="qr";e.textContent=f(T.rd,{x:x,n:C.length});d.appendChild(e);if(x==C.length)r.classList.add("done")})
})();
