# -*- coding: utf-8 -*-
import os, ad_lib as A
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageMath
FD=A.FD; CH=os.environ.get("VE_CHEROES","cheroes")
INK=A.INK; GOLD=A.GOLD; OFF=A.OFF; LGOLD=A.LGOLD; MUT=A.MUT; INKP=(18,16,13)
OFFW=(244,238,227); HOOKC=(238,232,222); SUBC=(236,230,220); BACKC=(200,190,172)
W,H=1080,1350; M=44; FW=4; INSET=M+26
ADDR1="909 BAINES ST"; ADDR2="EAST PALO ALTO, CALIFORNIA"
_scr=ImageDraw.Draw(Image.new("RGB",(8,8)))
def FT(fn,s): return ImageFont.truetype(FD+fn,s)
def tw(t,fn,s,tr=0):
    f=FT(fn,s); return sum(_scr.textlength(c,font=f) for c in t)+tr*max(0,len(t)-1)
def fit(t,fn,s,maxw,tr=0):
    while s>20 and tw(t,fn,s,tr)>maxw: s-=2
    return s
def _ramp(w,h,start,maxa,power=1.3):
    col=Image.new("L",(1,h),0); px=col.load()
    for yy in range(h):
        tt=(yy/h-start)/max(1e-6,1-start); px[0,yy]=0 if tt<0 else min(255,int((tt**power)*maxa))
    return col.resize((w,h))
def _alpha(mode):
    if mode=="close":
        flat=Image.new("L",(W,H),120); rp=_ramp(W,H,0.20,235)
        return ImageChops.invert(ImageChops.multiply(ImageChops.invert(flat),ImageChops.invert(rp)))
    bot=_ramp(W,H,0.46 if mode=="cover" else 0.50,225 if mode=="cover" else 215)
    col2=Image.new("L",(1,H),0); p2=col2.load()
    for yy in range(H):
        tt=1-yy/(H*0.22); p2[0,yy]=0 if tt<0 else min(255,int(tt*95))
    return ImageChops.lighter(bot,col2.resize((W,H)))
def grad(img,mode):
    img.paste(Image.new("RGB",(W,H),(8,7,6)),(0,0),_alpha(mode)); return img
def grad_overlay(mode):
    ov=Image.new("RGBA",(W,H),(8,7,6,255)); ov.putalpha(_alpha(mode)); return ov

SLIDES=[
 dict(t="cover",hero="s01_cover.png",focal=(0.52,0.46),num=1,
      hook="Soaring ceilings  ·  granite kitchen  ·  private patio"),
 dict(t="feat",hero="s02_vault.png",focal=(0.50,0.42),num=2,label="VAULTED CEILINGS",
      sub="Soaring ceilings over the main living area"),
 dict(t="feat",hero="s03_living.png",focal=(0.50,0.50),num=3,label="OPEN-CONCEPT LIVING",
      sub="Bright living & dining that opens to the patio"),
 dict(t="feat",hero="s04_kitchen.png",focal=(0.50,0.55),num=4,label="GRANITE ISLAND KITCHEN",
      sub="A center island with seating and a gas range"),
 dict(t="feat",hero="s05_bed.png",focal=(0.50,0.50),num=5,label="BRIGHT BEDROOMS",
      sub="Sunny secondary bedrooms with warm accents"),
 dict(t="feat",hero="s06_loft.png",focal=(0.50,0.45),num=6,label="UPSTAIRS LOFT",
      sub="An open loft landing overlooks the living room"),
 dict(t="feat",hero="s07_primary.png",focal=(0.50,0.50),num=7,label="PRIMARY SUITE",
      sub="A spacious, light-filled primary bedroom"),
 dict(t="feat",hero="s08_shower.png",focal=(0.50,0.50),num=8,label="SPA-STYLE BATH",
      sub="Walk-in glass shower with a rainfall head"),
 dict(t="feat",hero="s09_patio.png",focal=(0.50,0.55),num=9,label="PRIVATE PATIO",
      sub="A pergola-shaded patio for outdoor living"),
 dict(t="close",hero="s10_close.png",focal=(0.52,0.48),num=10,
      recap=["Soaring vaulted ceilings","Open-concept living & dining","Granite island kitchen",
             "Spa-style walk-in shower","Private patio + attached garage"]),
]
def ops_for(spec):
    ops=[]; num=spec["num"]
    ctr=f"{num:02d} / 10"; cx=W-INSET-tw(ctr,"Poppins-Light.ttf",24,3)
    ops.append(("text",cx,M+30,ctr,"Poppins-Light.ttf",24,LGOLD,3))
    if spec["t"]=="cover":
        ops.append(("pill",INSET,M+24,"JUST LISTED","Poppins-Medium.ttf",25,"gold"))
    else:
        ops.append(("text",INSET,M+30,ADDR1,"Poppins-Medium.ttf",22,OFFW,3))
    if spec["t"]=="cover":
        y=H-M-70; ssz=29
        ops.append(("text",INSET,y-ssz,"SWIPE TO TOUR","Poppins-Medium.ttf",ssz,GOLD,2))
        ops.append(("chev",INSET+tw("SWIPE TO TOUR","Poppins-Medium.ttf",ssz,2)+16,y-ssz+4,ssz-6,GOLD,4))
        yh=y-ssz-46; hs=fit(spec["hook"],"Poppins-Light.ttf",30,W-2*INSET)
        ops.append(("text",INSET,yh-hs,spec["hook"],"Poppins-Light.ttf",hs,HOOKC,0))
        yr=yh-hs-22; ops.append(("rule",INSET,yr,96,5,GOLD))
        yc=yr-16; ops.append(("text",INSET,yc-33,ADDR2,"Poppins-Light.ttf",27,LGOLD,4))
        asz=fit(ADDR1,"Poppins-Bold.ttf",96,W-2*INSET); ya=yc-33-asz-10
        ops.append(("text",INSET,ya-asz,ADDR1,"Poppins-Bold.ttf",asz,OFF,0))
    elif spec["t"]=="feat":
        ss=fit(spec["sub"],"Poppins-Light.ttf",30,W-2*INSET); ls=fit(spec["label"],"Poppins-Bold.ttf",62,W-2*INSET)
        ybase=H-M-78
        ops.append(("text",INSET,ybase-ss,spec["sub"],"Poppins-Light.ttf",ss,SUBC,0))
        yl=ybase-ss-16-ls; ops.append(("text",INSET,yl-ls,spec["label"],"Poppins-Bold.ttf",ls,OFF,0))
        yr=yl-ls-20; ops.append(("rule",INSET,yr,80,5,GOLD))
    else:
        ya=720; asz=fit(ADDR1,"Poppins-Bold.ttf",66,W-2*INSET)
        ops.append(("text",INSET,ya,ADDR1,"Poppins-Bold.ttf",asz,OFF,0))
        ops.append(("text",INSET,ya+asz+10,ADDR2,"Poppins-Light.ttf",24,LGOLD,4))
        yr=ya+asz+50; ops.append(("rule",INSET,yr,80,5,GOLD))
        yy=yr+34
        for it in spec["recap"]:
            ops.append(("dot",INSET+6,yy+18,6,GOLD))
            ops.append(("text",INSET+30,yy,it,"Poppins-Light.ttf",30,SUBC,0)); yy+=52
        yy+=14
        ops.append(("text",INSET,yy,"NOW AVAILABLE IN EAST PALO ALTO","Poppins-Medium.ttf",29,GOLD,1)); yy+=52
        ops.append(("chev",INSET+2,yy+4,18,MUT,3))
        ops.append(("text",INSET+26,yy,"Swipe back to tour again","Poppins-Light.ttf",24,BACKC,0))
    return ops
def _tdraw(d,x,y,t,fn,s,col,tr=0):
    f=FT(fn,s)
    for c in t: d.text((x,y),c,font=f,fill=col); x+=d.textlength(c,font=f)+tr
def _pill(img,d,x,y,text,fn,s,style):
    f=FT(fn,s); asc,_=f.getmetrics(); capH=int(asc*0.70); tr=4
    twi=tw(text,fn,s,tr); padx=int(s*1.05); pady=int(s*0.72); pw=twi+2*padx; ph=capH+2*pady; rad=ph//2
    if style=="gold": d.rounded_rectangle([x,y,x+pw,y+ph],rad,fill=GOLD); tc=INK
    else: d.rounded_rectangle([x,y,x+pw,y+ph],rad,fill=INKP,outline=GOLD,width=3); tc=OFF
    ty=y+(ph-capH)//2-int(asc*0.30); _tdraw(d,x+padx,ty,text,fn,s,tc,tr)
def paint_pil(img,ops):
    d=ImageDraw.Draw(img,"RGBA")
    for op in ops:
        k=op[0]
        if k=="text": _,x,y,t,fn,s,col,tr=op; _tdraw(d,x,y,t,fn,s,col,tr)
        elif k=="rule": _,x,y,w,h,col=op; d.rectangle([x,y,x+w,y+h],fill=col)
        elif k=="dot": _,cx,cy,r,col=op; d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=col)
        elif k=="pill": _,x,y,t,fn,s,st=op; _pill(img,d,x,y,t,fn,s,st)
        elif k=="chev": _,x,y,h,col,wt=op; d.line([(x,y),(x+h*0.55,y+h/2)],fill=col,width=wt); d.line([(x,y+h),(x+h*0.55,y+h/2)],fill=col,width=wt)
def render(i,mode="png"):
    spec=SLIDES[i]; img=A.crop_to(Image.open(CH+"/"+spec["hero"]).convert("RGB"),W,H,spec["focal"])
    if mode=="clean": return img
    grad(img,spec["t"]); d=ImageDraw.Draw(img,"RGBA"); d.rectangle([M,M,W-M-1,H-M-1],outline=GOLD,width=FW)
    paint_pil(img,ops_for(spec)); return img
