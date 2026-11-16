#!/usr/bin/env python3
"""给 JPEG 写入出处（XMP），不重压图片：只在文件头插一段 APP1，像素字节原样不动。
用法：python3 chuchu_xmp.py 图.jpg --url https://yikonglu.com/lunyu/1.6 --desc "论语集注 朱熹 卷一 学而 · 第 17 页" [--license https://creativecommons.org/licenses/by/4.0/] [-o 输出.jpg]
不给 --license 就不写许可（原页扫描的底本权利归原藏家或公版，不替人声明）。已有本工具写的 XMP 会先去掉再写，可反复跑。"""
import argparse, struct, sys
from xml.sax.saxutils import escape

NS = b'http://ns.adobe.com/xap/1.0/\x00'

def xmp(url, desc, lic):
    e = lambda s: escape(s, {'"': '&quot;'})
    lic_attr = f'\n   xmpRights:Marked="True" cc:license="{e(lic)}"' if lic else ''
    rights = f'一孔录 yikonglu.com · {"CC BY 4.0" if lic and "/by/4.0" in lic else "出处见 " + url}'
    return f'''<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
 <rdf:Description rdf:about=""
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/"
   xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
   xmlns:cc="http://creativecommons.org/ns#"
   photoshop:Credit="一孔录 yikonglu.com"
   photoshop:Source="{e(url)}"
   xmpRights:WebStatement="{e(url)}"{lic_attr}>
  <dc:creator><rdf:Seq><rdf:li>一孔录 yikonglu.com</rdf:li></rdf:Seq></dc:creator>
  <dc:source>{e(url)}</dc:source>
  <dc:description><rdf:Alt><rdf:li xml:lang="x-default">{e(desc)}</rdf:li></rdf:Alt></dc:description>
  <dc:rights><rdf:Alt><rdf:li xml:lang="x-default">{e(rights)}</rdf:li></rdf:Alt></dc:rights>
 </rdf:Description>
</rdf:RDF></x:xmpmeta>
<?xpacket end="w"?>'''.encode('utf-8')

def stamp(data, packet):
    assert data[:2] == b'\xff\xd8', '不是 JPEG'
    i, segs = 2, []
    while True:  # 读到 SOS 为止的各段
        assert data[i] == 0xFF
        m = data[i+1]
        if m == 0xDA: break
        n = struct.unpack('>H', data[i+2:i+4])[0]
        segs.append((m, data[i:i+2+n])); i += 2 + n
    rest = data[i:]
    segs = [s for s in segs if not (s[0] == 0xE1 and s[1][4:4+len(NS)] == NS)]  # 去旧 XMP
    body = NS + packet
    assert len(body) + 2 < 65536
    app1 = b'\xff\xe1' + struct.pack('>H', len(body) + 2) + body
    # 放在 APP0(JFIF)/EXIF 之后
    k = 0
    while k < len(segs) and segs[k][0] in (0xE0, 0xE1): k += 1
    segs.insert(k, (0xE1, app1))
    return b'\xff\xd8' + b''.join(s for _, s in segs) + rest

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('jpg'); a.add_argument('--url', required=True); a.add_argument('--desc', required=True)
    a.add_argument('--license'); a.add_argument('-o')
    o = a.parse_args()
    d = open(o.jpg, 'rb').read()
    open(o.o or o.jpg, 'wb').write(stamp(d, xmp(o.url, o.desc, o.license)))
