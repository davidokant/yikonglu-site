# 导出已公开各章的原文句、定版白话、引文取处到 pub.json，供 gen.py 用。用法：python3 tools/zhuju_gen/dump.py <读法札记> x tools/zhuju_gen/pub.json
import sys,os,json
sys.path.insert(0,'tools')
import build as B
def dump(L,D,w):
    out={}
    for c in D["pub"]:
        out[c]={"ju":B.split_ju(D["yw"][c]),"bh":D["baihua"].get(c),"cites":[[x["text"],x["src"],x["pages"],x["para"]] for x in D["gao"].get(c,{}).get("cites",[])],
                "gist":(D["notes"][c].get("片里落点") if isinstance(D["notes"][c],dict) else None)}
    json.dump(out,open(sys.argv[3],'w',encoding='utf-8'),ensure_ascii=False,indent=1); os._exit(0)
B.build_lang=dump
B.main(sys.argv[1],'/tmp/claude-0/-home-user-yikonglu-site/c0c9f10f-2841-51ec-8cc4-eb5d40f51509/scratchpad/docs_tmp')
