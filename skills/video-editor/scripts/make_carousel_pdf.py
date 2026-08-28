import carousel_lib as C, ad_lib as A, os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import ImageFont
FD=A.FD; W,H=C.W,C.H; OUT=os.environ.get("VE_CAROUSEL_PDF","carousel-editable.pdf")
TMP=os.environ.get("VE_TMP","./.ve_ctmp"); os.makedirs(TMP,exist_ok=True)
for nm in ["Poppins-Bold","Poppins-Medium","Poppins-Light"]:
    pdfmetrics.registerFont(TTFont(nm,FD+nm+".ttf"))
def col(c): return Color(c[0]/255,c[1]/255,c[2]/255)
def asc(fn,s): return ImageFont.truetype(FD+fn,s).getmetrics()[0]
def rtext(cv,x,ybase,t,fn,s,tr,color):
    cv.setFillColor(color); cv.setFont(fn[:-4],s)
    for ch in t: cv.drawString(x,ybase,ch); x+=cv.stringWidth(ch,fn[:-4],s)+tr
def paint_pdf(cv,ops):
    for op in ops:
        k=op[0]
        if k=="text":
            _,x,y,t,fn,s,c,tr=op; rtext(cv,x,H-(y+asc(fn,s)),t,fn,s,tr,col(c))
        elif k=="rule":
            _,x,y,w,h,c=op; cv.setFillColor(col(c)); cv.rect(x,H-(y+h),w,h,fill=1,stroke=0)
        elif k=="dot":
            _,cx,cy,r,c=op; cv.setFillColor(col(c)); cv.circle(cx,H-cy,r,fill=1,stroke=0)
        elif k=="pill":
            _,x,y,t,fn,s,st=op
            a=asc(fn,s); capH=int(a*0.70); tr=4
            twi=C.tw(t,fn,s,tr); padx=int(s*1.05); pady=int(s*0.72); pw=twi+2*padx; ph=capH+2*pady; rad=ph/2; yb=H-(y+ph)
            if st=="gold": cv.setFillColor(col(C.GOLD)); cv.roundRect(x,yb,pw,ph,rad,fill=1,stroke=0); tc=col(C.INK)
            else:
                cv.setFillColor(col(C.INKP)); cv.setStrokeColor(col(C.GOLD)); cv.setLineWidth(3); cv.roundRect(x,yb,pw,ph,rad,fill=1,stroke=1); tc=col(C.OFF)
            ty=y+(ph-capH)//2-int(a*0.30); rtext(cv,x+padx,H-(ty+a),t,fn,s,tr,tc)
        elif k=="chev":
            _,x,y,h,c,wt=op; cv.setStrokeColor(col(c)); cv.setLineWidth(wt); cv.setLineCap(1)
            cv.line(x,H-y,x+h*0.55,H-(y+h/2)); cv.line(x,H-(y+h),x+h*0.55,H-(y+h/2))
cv=canvas.Canvas(OUT,pagesize=(W,H))
for i,spec in enumerate(C.SLIDES):
    bg=f"{TMP}/{i}_clean.png"; C.render(i,"clean").save(bg)
    ov=f"{TMP}/{i}_grad.png"; C.grad_overlay(spec["t"]).save(ov)
    cv.drawImage(bg,0,0,W,H); cv.drawImage(ov,0,0,W,H,mask='auto')
    cv.setStrokeColor(col(C.GOLD)); cv.setLineWidth(C.FW); cv.rect(C.M,C.M,W-2*C.M,H-2*C.M,fill=0,stroke=1)
    paint_pdf(cv,C.ops_for(spec)); cv.showPage()
cv.save(); print("PDF ->",os.path.basename(OUT))
