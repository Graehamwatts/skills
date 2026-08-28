#!/usr/bin/env python3
"""Resumable listing-video editor. Usage: python3 edit_pipeline.py plan.json [--finish]

Plan JSON:
{
  "name": "r1", "workdir": "/tmp/edit", "out": "/tmp/edit/REEL1_FINAL_9x16.mp4",
  "width": 1080, "height": 1920, "fps": 25, "crf": 18,
  "audio_src": "/tmp/edit/reel1_avatar.mp4",        # full-length VO master (avatar render)
  "music": "/tmp/edit/music/track.wav", "music_vol": 0.10, "fade_out_start": 48.5,
  "segments": [   # timeline order; durations must sum to audio_src duration
    {"kind":"ai",     "src":"walk.mp4",  "dur":5.9},
    {"kind":"av",     "src":"reel1_avatar.mp4", "start":8.9, "dur":6.7},
    {"kind":"raw916", "src":".../C4401.MP4", "dur":2.95, "off":0.5},
    {"kind":"raw169", "src":".../C4391.MP4", "dur":6.0,  "off":0.3},
    {"kind":"img",    "src":".../photo.jpg", "dur":5.8}
  ],
  "overlays": [   # global timeline seconds
    {"text":"6,500 SQ FT LOT","font":"fonts/DMSans.ttf","size":84,"color":"0xE3C567",
     "y":"h*0.68","a":25.0,"b":31.0,"box":"black@0.45"}
  ]
}
Rules encoded: segments write to .tmp then rename (timeout-safe); re-run same command to resume.
For >130s videos run once (segments), then with --finish twice if the overlay+mux pass times out
(it splits automatically at the midpoint segment boundary).
"""
import subprocess, sys, os, json

plan = json.load(open(sys.argv[1]))
E = plan['workdir']; os.makedirs(f"{E}/seg", exist_ok=True)
name, W, H, FPS = plan['name'], plan['width'], plan['height'], plan.get('fps', 25)
CRF = str(plan.get('crf', 18))
ENC = ['-c:v','libx264','-preset','veryfast','-crf',CRF,'-pix_fmt','yuv420p','-an']

def cmd_for(s, out):
    d = s['dur']; off = s.get('off', 0)
    scale = f"fps={FPS},scale={W}:{H},setsar=1"
    pad = f"tpad=stop_mode=clone:stop_duration=20,trim=duration={d}"
    if s['kind'] == 'av':
        return ['ffmpeg','-y','-loglevel','error','-ss',str(s['start']),'-t',str(d),'-i',s['src'],'-vf',scale]+ENC+[out]
    if s['kind'] == 'ai':
        return ['ffmpeg','-y','-loglevel','error','-i',s['src'],'-vf',f'{scale},{pad}']+ENC+[out]
    if s['kind'] == 'raw169':
        return ['ffmpeg','-y','-loglevel','error','-ss',str(off),'-i',s['src'],'-vf',f'{scale},{pad}']+ENC+[out]
    if s['kind'] == 'raw916':  # 4K 16:9 -> vertical center crop
        crop = f"crop=ih*{W}/{H}:ih:(iw-ih*{W}/{H})/2:0"
        return ['ffmpeg','-y','-loglevel','error','-ss',str(off),'-i',s['src'],'-vf',f'fps={FPS},{crop},scale={W}:{H},setsar=1,{pad}']+ENC+[out]
    if s['kind'] == 'img':
        return ['ffmpeg','-y','-loglevel','error','-loop','1','-t',str(d),'-i',s['src'],'-vf',
                f"scale={int(W*1.25)}:-1,zoompan=z='1+0.0012*on':d=1:x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={W}x{H}:fps={FPS},trim=duration={d}"]+ENC+[out]
    raise ValueError(s['kind'])

files = []
for i, s in enumerate(plan['segments']):
    o = f"{E}/seg/{name}_{i:02d}.mp4"; files.append(o)
    if os.path.exists(o) and os.path.getsize(o) > 1000:
        continue
    tmp = o + '.tmp.mp4'
    cmd = [c if c != o else tmp for c in cmd_for(s, o)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print('SEGFAIL', i, r.stderr[-300:]); sys.exit(1)
    os.rename(tmp, o)
    print('seg', i, 'ok', flush=True)
print('ALL_SEGS_DONE')

def dt(ovs, shift=0.0):
    parts = []
    for ov in ovs:
        t = ov['text'].replace("'", "’").replace(':', '\\:').replace(',', '\\,')
        parts.append(
            f"drawtext=fontfile={ov['font']}:text='{t}':fontsize={ov['size']}:fontcolor={ov['color']}"
            f":x=(w-text_w)/2:y={ov['y']}:box=1:boxcolor={ov.get('box','black@0.45')}:boxborderw=16"
            f":enable='between(t,{ov['a']-shift},{ov['b']-shift})'")
    return ','.join(parts) if parts else 'null'

total = sum(s['dur'] for s in plan['segments'])
fade = plan.get('fade_out_start', total - 2.5)

def concat(lst_path, seg_files, out):
    open(lst_path,'w').write('\n'.join(f"file '{f}'" for f in seg_files))
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',lst_path,'-c','copy',out], check=True)

def mux(video, out):
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',video,'-i',plan['audio_src'],'-stream_loop','-1','-i',plan['music'],
        '-filter_complex', f"[2:a]volume={plan.get('music_vol',0.1)}[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=3,afade=t=out:st={fade}:d=2.4[a]",
        '-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest', out], check=True)

if total <= 130:
    cat = f"{E}/seg/{name}_cat.mp4"
    if not os.path.exists(cat): concat(f"{E}/seg/{name}.txt", files, cat)
    ov = f"{E}/seg/{name}_ov.mp4"
    if not os.path.exists(ov):
        tmp = ov + '.tmp.mp4'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',cat,'-vf',dt(plan['overlays']),
                        '-c:v','libx264','-preset','veryfast','-crf',CRF,'-pix_fmt','yuv420p','-an',tmp], check=True)
        os.rename(tmp, ov)
    mux(ov, plan['out']); print('DONE', plan['out'])
else:
    # split at segment boundary nearest the midpoint; each half resumable
    acc, split_i = 0.0, None
    for i, s in enumerate(plan['segments']):
        acc += s['dur']
        if acc >= total/2: split_i = i+1; break
    t_split = sum(s['dur'] for s in plan['segments'][:split_i])
    halves = [('A', files[:split_i], [o for o in plan['overlays'] if o['b'] <= t_split+1], 0.0),
              ('B', files[split_i:], [o for o in plan['overlays'] if o['a'] >= t_split-1], t_split)]
    for tag, fl, ovs, shift in halves:
        ovout = f"{E}/seg/{name}_{tag}_ov.mp4"
        if os.path.exists(ovout): print(tag,'skip'); continue
        cat = f"{E}/seg/{name}_{tag}.mp4"
        if not os.path.exists(cat): concat(f"{E}/seg/{name}_{tag}.txt", fl, cat)
        tmp = ovout + '.tmp.mp4'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',cat,'-vf',dt(ovs,shift),
                        '-c:v','libx264','-preset','ultrafast','-crf',CRF,'-pix_fmt','yuv420p','-an',tmp], check=True)
        os.rename(tmp, ovout)
        print(tag, 'ov done', flush=True)
    catF = f"{E}/seg/{name}_F.mp4"
    concat(f"{E}/seg/{name}_F.txt", [f"{E}/seg/{name}_A_ov.mp4", f"{E}/seg/{name}_B_ov.mp4"], catF)
    mux(catF, plan['out']); print('DONE', plan['out'])
