import ad_lib as A, os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageDraw, ImageFont
FD=A.FD; KIT=os.environ.get("VE_KIT","ad-kit")
TMP=KIT+"/.tmp"; os.makedirs(TMP,exist_ok=True)
for nm,fn in [("Poppins-Bold","Poppins-Bold.ttf"),("Poppins-Medium","Poppins-Medium.ttf"),("Poppins-Light","Poppins-Light.ttf")]:
    pdfmetrics.registerFont(TTFont(nm,FD+fn))
GOLD=HexColor("#C7A974"); INK=HexColor("#0E0C0A"); OFF=HexColor("#F4EEE3"); LGOLD=HexColor("#DEC9A2"); INKP=HexColor("#12100D")
scr=ImageDraw.Draw(Image.new("RGB",(8,8)))
def tlen(t,f,tr): return sum(scr.textlength(c,font=f) for c in t)+tr*max(0,len(t)-1)
def rtext(c,x,y,text,font,size,tr,col):
    c.setFillColor(col); c.setFont(font,size)
    for ch in text:
        c.drawString(x,y,ch); x+=c.stringWidth(ch,font,size)+tr
order=["Exterior","Interior","Detail"]
for skey,s in A.SIZES.items():
    w,h=s["w"],s["h"]; pdf=f"{KIT}/Canva-Editable-PDF/909Baines_Ads_{skey}.pdf"
    c=canvas.Canvas(pdf,pagesize=(w,h))
    for cn in order:
        cc=A.CONCEPTS[cn]
        bg=f"{TMP}/{cn}_{skey}_clean.png"; A.render(cn,skey,"clean").save(bg)
        ov=f"{TMP}/{cn}_{skey}_grad.png"; A.grad_overlay(w,h,s["gstart"],s["gmax"]).save(ov)
        c.drawImage(bg,0,0,w,h); c.drawImage(ov,0,0,w,h,mask='auto')
        m=s["margin"]; c.setStrokeColor(GOLD); c.setLineWidth(s["fw"]); c.rect(m,m,w-2*m,h-2*m,fill=0,stroke=1)
        fM=ImageFont.truetype(FD+"Poppins-Medium.ttf",s["stamp"]); ascM,_=fM.getmetrics(); capH=int(ascM*0.70)
        tr=s["stamp"]*0.16; tw=tlen(cc["stamp"],fM,tr); padx=int(s["stamp"]*1.05); pady=int(s["stamp"]*0.72)
        pw=tw+2*padx; ph=capH+2*pady; px=m+int(w*0.022); py=m+int(h*0.026); yb=h-(py+ph)
        if cc["style"]=="gold":
            c.setFillColor(GOLD); c.roundRect(px,yb,pw,ph,ph/2,fill=1,stroke=0); tcol=INK
        else:
            c.setFillColor(INKP); c.setStrokeColor(GOLD); c.setLineWidth(max(2,s["fw"]-1)); c.roundRect(px,yb,pw,ph,ph/2,fill=1,stroke=1); tcol=OFF
        ty=py+(ph-capH)//2-int(ascM*0.30)
        rtext(c,px+padx,h-(ty+ascM),cc["stamp"],"Poppins-Medium",s["stamp"],tr,tcol)
        left=m+int(w*0.030)
        fa=ImageFont.truetype(FD+"Poppins-Bold.ttf",s["addr"]); aasc,adesc=fa.getmetrics(); ah=aasc+adesc
        fc=ImageFont.truetype(FD+"Poppins-Light.ttf",s["city"]); cAsc,cDesc=fc.getmetrics(); chh=cAsc+cDesc
        trc=s["city"]*0.16; gapb=int(h*0.055)
        y_city=h-m-gapb-chh; y_rule=y_city-int(h*0.020); y_addr=y_rule-int(h*0.012)-ah
        c.setFillColor(OFF); c.setFont("Poppins-Bold",s["addr"]); c.drawString(left,h-(y_addr+aasc),A.ADDR1)
        thick=max(2,int(h*0.0045)); rl=int(w*0.085)
        c.setFillColor(GOLD); c.rect(left,h-(y_rule+thick),rl,thick,fill=1,stroke=0)
        rtext(c,left,h-(y_city+cAsc),A.ADDR2,"Poppins-Light",s["city"],trc,LGOLD)
        c.showPage()
    c.save(); print("PDF",os.path.basename(pdf))
