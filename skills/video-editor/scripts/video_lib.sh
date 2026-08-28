#!/bin/bash
SRC="${VE_SRC:?set VE_SRC to the folder of raw property clips}"
B="${VE_OUT:-./ve_build}"
FONT="${VE_FONT:-/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf}"
GRADE_STD="eq=contrast=1.06:saturation=1.10:brightness=0.004:gamma=0.99,unsharp=3:3:0.4:3:3:0.0"
GRADE_HERO="eq=contrast=1.05:saturation=1.00,colorbalance=rm=-0.04:rh=-0.03:bm=0.02,unsharp=3:3:0.4:3:3:0.0"
mkdir -p "$B"
ENC="-an -r 30 -c:v libx264 -preset veryfast -crf 17 -pix_fmt yuv420p -video_track_timescale 30000"

# fade alpha expr, local segment time, appear A disappear B with 0.4s ramps
af(){ local A=$1 Bt=$2; echo "if(lt(t,$A),0,if(lt(t,$A+0.4),(t-$A)/0.4,if(lt(t,$Bt-0.4),1,if(lt(t,$Bt),($Bt-t)/0.4,0))))"; }

# feature label bottom-left: $1 text $2 appear $3 disappear  (for 1920x1080)
label16(){ local T="$1" A="$2" D="$3"; local al=$(af "$A" "$D")
 echo "drawbox=x=82:y=h-148:w=54:h=7:color=0xC79A33:t=fill:enable='between(t,$A,$D)',drawtext=fontfile=$FONT:text='$T':x=82:y=h-128:fontsize=44:fontcolor=white:shadowcolor=black@0.6:shadowx=2:shadowy=2:alpha='$al'"; }

# centered title 1920x1080: $1 big $2 small $3 appear $4 disappear
title16(){ local T1="$1" T2="$2" A="$3" D="$4"; local al=$(af "$A" "$D")
 echo "drawtext=fontfile=$FONT:text='$T1':x=(w-text_w)/2:y=h/2-40:fontsize=78:fontcolor=white:shadowcolor=black@0.55:shadowx=2:shadowy=3:alpha='$al',drawbox=x=(w-150)/2:y=h/2+58:w=150:h=6:color=0xC79A33:t=fill:enable='between(t,$A,$D)',drawtext=fontfile=$FONT:text='$T2':x=(w-text_w)/2:y=h/2+78:fontsize=34:fontcolor=0xEAEAEA:alpha='$al'"; }

# reel caption centered upper third 1080x1920: $1 text $2 appear $3 disappear
capR(){ local T="$1" A="$2" D="$3"; local al=$(af "$A" "$D")
 echo "drawtext=fontfile=$FONT:text='$T':x=(w-text_w)/2:y=560:fontsize=66:fontcolor=white:shadowcolor=black@0.7:shadowx=2:shadowy=2:box=1:boxcolor=black@0.18:boxborderw=22:alpha='$al',drawbox=x=(w-120)/2:y=648:w=120:h=7:color=0xC79A33:t=fill:enable='between(t,$A,$D)'"; }

# 16:9 segment: SRC SS DUR OUT GRADE POST
seg16(){ local s="$1" ss="$2" du="$3" out="$4" gr="${5:-$GRADE_STD}" post="$6"
 local vf="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,$gr"
 [ -n "$post" ] && vf="$vf,$post"
 vf="$vf,fps=30,format=yuv420p,setsar=1"
 ffmpeg -nostdin -v error -ss "$ss" -t "$du" -i "$SRC/$s" -vf "$vf" $ENC "$B/$out" -y; }

# 9:16 center-crop: SRC SS DUR OUT GRADE POST XOFF
seg916c(){ local s="$1" ss="$2" du="$3" out="$4" gr="${5:-$GRADE_STD}" post="$6" xo="${7:-0}"
 local vf="crop=ih*9/16:ih:(iw-ih*9/16)/2+($xo):0,scale=1080:1920,$gr"
 [ -n "$post" ] && vf="$vf,$post"
 vf="$vf,fps=30,format=yuv420p,setsar=1"
 ffmpeg -nostdin -v error -ss "$ss" -t "$du" -i "$SRC/$s" -vf "$vf" $ENC "$B/$out" -y; }

# 9:16 blurred-pad: SRC SS DUR OUT GRADE POST
seg916p(){ local s="$1" ss="$2" du="$3" out="$4" gr="${5:-$GRADE_STD}" post="$6"
 local chain="[0:v]$gr,split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=24:steps=2[b];[fg]scale=1080:-2[f];[b][f]overlay=(W-w)/2:(H-h)/2[o]"
 if [ -n "$post" ]; then chain="$chain;[o]$post,fps=30,format=yuv420p,setsar=1[v]"; else chain="$chain;[o]fps=30,format=yuv420p,setsar=1[v]"; fi
 ffmpeg -nostdin -v error -ss "$ss" -t "$du" -i "$SRC/$s" -filter_complex "$chain" -map "[v]" $ENC "$B/$out" -y; }

# xfade two seg files: A B STYLE DUR OUT
xf(){ local a="$1" b="$2" st="$3" d="$4" out="$5"
 local da=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$B/$a"); local off=$(echo "$da-$d"|bc)
 ffmpeg -nostdin -v error -i "$B/$a" -i "$B/$b" -filter_complex "[0:v]settb=AVTB[x];[1:v]settb=AVTB[y];[x][y]xfade=transition=$st:duration=$d:offset=$off,format=yuv420p[v]" -map "[v]" -r 30 -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -video_track_timescale 30000 "$B/$out" -y; }
