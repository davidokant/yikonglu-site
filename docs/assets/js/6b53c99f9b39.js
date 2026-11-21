(function(){var F=document.querySelector('.yuanwen.dz.nocard');if(!F)return;var Q=F.querySelector('blockquote');
function hl(n){F.querySelectorAll('.yyp .hl').forEach(function(r){r.classList.toggle('on',r.dataset.s==n)});var r=F.querySelector('.yyp .hl[data-s="'+n+'"]'),P=F.querySelector('.yypane');
if(r&&P&&P.scrollHeight>P.clientHeight+4){var a=r.getBoundingClientRect(),b=P.getBoundingClientRect();P.scrollTo({top:P.scrollTop+a.top-b.top-(b.height-a.height)/2,behavior:'smooth'})}}
Q.addEventListener('click',function(e){var s=e.target.closest('.ju');if(!s)return;F.querySelectorAll('.ju.lit').forEach(function(x){x.classList.remove('lit')});s.classList.add('lit');hl(s.dataset.n)});
var h=location.hash.slice(1);if(/^s\d+$/.test(h)){var t=document.getElementById(h);if(t&&Q.contains(t))setTimeout(function(){hl(t.dataset.n)},300)}})();
