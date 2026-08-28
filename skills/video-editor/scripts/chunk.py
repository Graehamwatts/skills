import sys, subprocess
def dur(f):
    o=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).decode().strip()
    return float(o)
# usage: chunk.py OUT FADEIN FADEOUT seg1 [T D seg]...
out=sys.argv[1]; fin=float(sys.argv[2]); fout=float(sys.argv[3])
rest=sys.argv[4:]
segs=[rest[0]]; trans=[]; dts=[]
i=1
while i < len(rest):
    trans.append(rest[i]); dts.append(float(rest[i+1])); segs.append(rest[i+2]); i+=3
n=len(segs); durs=[dur(s) for s in segs]
fc=[]
for i in range(n):
    fc.append(f"[{i}:v]settb=AVTB,format=yuv420p,fps=30[v{i}]")
acc="[v0]"; accdur=durs[0]
for i in range(1,n):
    off=accdur-dts[i-1]
    lbl=f"[x{i}]"
    fc.append(f"{acc}[v{i}]xfade=transition={trans[i-1]}:duration={dts[i-1]}:offset={off:.3f}{lbl}")
    accdur=accdur+durs[i]-dts[i-1]
    acc=lbl
fades=[]
if fin>0: fades.append(f"fade=t=in:st=0:d={fin}")
if fout>0: fades.append(f"fade=t=out:st={max(0,accdur-fout):.3f}:d={fout}")
if fades:
    fc.append(f"{acc}{','.join(fades)}[outv]"); acc="[outv]"
elif n==1:
    fc.append(f"{acc}null[outv]"); acc="[outv]"
inputs=[]
for s in segs: inputs+=["-i",s]
cmd=["ffmpeg","-nostdin","-v","error",*inputs,"-filter_complex",";".join(fc),"-map",acc,
     "-r","30","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-video_track_timescale","30000",out,"-y"]
subprocess.check_call(cmd)
print(f"{out}  dur={accdur:.2f}s  segs={n}")
