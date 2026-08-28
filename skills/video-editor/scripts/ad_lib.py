# -*- coding: utf-8 -*-
import sys, os
from PIL import Image, ImageDraw, ImageFont
HERO=os.environ.get("VE_HERO","heroes")
def _find_font_dir():
    import os
    cands=[os.environ.get("VE_FONTDIR"),"/usr/share/fonts/truetype/google-fonts/",
           "/usr/share/fonts/truetype/poppins/",os.path.expanduser("~/.fonts/"),
           os.path.join(os.path.dirname(os.path.abspath(__file__)),"fonts")+"/"]
    for d in cands:
        if d and os.path.exists(os.path.join(d,"Poppins-Bold.ttf")):
            return d if d.endswith("/") else d+"/"
    raise SystemExit("Poppins TTFs not found. Install (apt-get install fonts-poppins / fonts-google-poppins) or set VE_FONTDIR to a folder containing Poppins-Bold.ttf etc.")
FD=_find_font_dir()
INK=(14,12,10); GOLD=(199,169,116); OFF=(244,238,227); LGOLD=(222,201,162); MUT=(187,171,142)
def F(name,sz): return ImageFont.truetype(FD+name, sz)
SIZES={
 "1080x1350-IG-Portrait": dict(w=1080,h=1350, addr=86, city=25, stamp=25, margin=44, fw=4, gstart=0.46, gmax=210),
 "1080x1080-Square":      dict(w=1080,h=1080, addr=78, city=24, stamp=24, margin=40, fw=4, gstart=0.46, gmax=210),
 "1200x628-Landscape":    dict(w=1200,h=628,  addr=62, city=20, stamp=21, margin=30, fw=3, gstart=0.38, gmax=205),
}
CONCEPTS={
 "Exterior":  dict(hero="hero_exterior.png", stamp="JUST LISTED", style="gold", focal=(0.52,0.45)),
 "Interior":  dict(hero="hero_interior.png", stamp="NEW LISTING", style="ink",  focal=(0.50,0.46)),
 "Detail":    dict(hero="hero_detail.png",   stamp="JUST LISTED", style="gold", focal=(0.50,0.52)),
}
ADDR1="909 BAINES ST"; ADDR2="EAST PALO ALTO, CALIFORNIA"

def crop_to(img,w,h,focal):
    iw,ih=img.size; tgt=w/h; src=iw/ih
    if src>tgt: nw=int(round(ih*tgt)); nh=ih
    else: nw=iw; nh=int(round(iw/tgt))
    fx,fy=focal; x=int(fx*iw-nw/2); y=int(fy*ih-nh/2)
    x=max(0,min(iw-nw,x)); y=max(0,min(ih-nh,y))
    return img.crop((x,y,x+nw,y+nh)).resize((w,h),Image.LANCZOS)

def vgrad(img,start,maxa,top=True):
    w,h=img.size
    col=Image.new("L",(1,h),0); px=col.load()
    for yy in range(h):
        t=(yy/h-start)/max(1e-6,(1-start)); px[0,yy]=0 if t<0 else min(255,int((t**1.3)*maxa))
    img.paste(Image.new("RGB",(w,h),(7,6,5)),(0,0),col.resize((w,h)))
    if top:
        col2=Image.new("L",(1,h),0); p2=col2.load()
        for yy in range(h):
            t=1-yy/(h*0.20); p2[0,yy]=0 if t<0 else min(255,int(t*80))
        img.paste(Image.new("RGB",(w,h),(7,6,5)),(0,0),col2.resize((w,h)))
    return img

def tlen(d,t,f,tr=0): return sum(d.textlength(c,font=f) for c in t)+tr*max(0,len(t)-1)
def tdraw(d,xy,t,f,fill,tr=0):
    x,y=xy
    for c in t:
        d.text((x,y),c,font=f,fill=fill); x+=d.textlength(c,font=f)+tr
    return x

def pill(img,d,x,y,text,style,szcfg):
    f=F("Poppins-Medium.ttf",szcfg["stamp"]); tr=szcfg["stamp"]*0.16
    asc,desc=f.getmetrics(); capH=int(asc*0.70)
    tw=tlen(d,text,f,tr); padx=int(szcfg["stamp"]*1.05); pady=int(szcfg["stamp"]*0.72)
    pw=tw+2*padx; ph=capH+2*pady; rad=ph//2
    if style=="gold": fillc=GOLD; txtc=INK; bd=None; bw=0
    else: fillc=(18,16,13); txtc=OFF; bd=GOLD; bw=max(2,szcfg["fw"]-1)
    d.rounded_rectangle([x,y,x+pw,y+ph],radius=rad,fill=fillc,outline=bd,width=bw)
    ty=y+(ph-capH)//2-int(asc*0.30)
    tdraw(d,(x+padx,ty),text,f,txtc,tr)
    return pw,ph

def render(concept,sizekey,mode="png"):
    c=CONCEPTS[concept]; s=SIZES[sizekey]; w,h=s["w"],s["h"]
    img=crop_to(Image.open(HERO+"/"+c["hero"]).convert("RGB"),w,h,c["focal"])
    if mode=="clean": return img
    vgrad(img,s["gstart"],s["gmax"])
    d=ImageDraw.Draw(img,"RGBA")
    inset=s["margin"]; d.rectangle([inset,inset,w-inset-1,h-inset-1],outline=GOLD,width=s["fw"])
    if mode=="plate": return img  # frame+gradient, no pill/text (for editable PDF)
    # stamp pill top-left
    px=inset+int(w*0.022); py=inset+int(h*0.026)
    pill(img,d,px,py,c["stamp"],c["style"],s)
    # address block lower-left
    left=inset+int(w*0.030)
    fa=F("Poppins-Bold.ttf",s["addr"]); fc=F("Poppins-Light.ttf",s["city"]); trc=s["city"]*0.16
    aasc,adesc=fa.getmetrics(); ah=aasc+adesc; cAsc,cDesc=fc.getmetrics(); chh=cAsc+cDesc
    gapb=int(h*0.055)
    y_city=h-inset-gapb-chh
    y_rule=y_city-int(h*0.020)
    y_addr=y_rule-int(h*0.012)-ah
    d.text((left,y_addr),ADDR1,font=fa,fill=OFF)
    rl=int(w*0.085); d.rectangle([left,y_rule,left+rl,y_rule+max(2,int(h*0.0045))],fill=GOLD)
    tdraw(d,(left,y_city),ADDR2,fc,LGOLD,trc)
    return img

if __name__=="__main__":
    if sys.argv[1]=="one":
        render(sys.argv[2],sys.argv[3],"png").save(sys.argv[4]); print("saved",sys.argv[4])

from PIL import ImageChops
def grad_overlay(w,h,start,maxa):
    col=Image.new("L",(1,h),0); px=col.load()
    for yy in range(h):
        t=(yy/h-start)/max(1e-6,(1-start)); px[0,yy]=0 if t<0 else min(255,int((t**1.3)*maxa))
    bot=col.resize((w,h))
    col2=Image.new("L",(1,h),0); p2=col2.load()
    for yy in range(h):
        t=1-yy/(h*0.20); p2[0,yy]=0 if t<0 else min(255,int(t*80))
    top=col2.resize((w,h))
    amax=ImageChops.lighter(bot,top)
    ov=Image.new("RGBA",(w,h),(7,6,5,255)); ov.putalpha(amax)
    return ov
