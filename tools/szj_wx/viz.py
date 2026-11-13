from PIL import Image,ImageDraw; import json,glob,os
D=json.load(open('pages.json')); CH=D['CH']
by={}
for k,(pg,boxes,gap) in CH.items(): by.setdefault(pg,[]).extend(boxes)
fs=sorted(glob.glob('out/p*.jpg')); th=[]
for f in fs:
    pg=os.path.basename(f)[:-4]; im=Image.open(f).convert('RGB'); d=ImageDraw.Draw(im)
    for i,b in enumerate(by.get(pg,[])): d.rectangle(b,outline=('red' if i%2 else 'blue'),width=5)
    d.text((10,10),pg,fill='red'); im.thumbnail((200,330)); th.append(im)
n=len(th); per=17; rows=(n+per-1)//per
S=Image.new('RGB',(per*202,rows*332),'white')
for i,t in enumerate(th): S.paste(t,((i%per)*202,(i//per)*332))
S.save('viz.jpg',quality=85); print(n,S.size)
