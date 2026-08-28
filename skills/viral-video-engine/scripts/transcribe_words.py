#!/usr/bin/env python3
"""Word-level timestamps for cut planning. Usage: python3 transcribe_words.py render.mp4 [out.json]
Requires: pip install faster-whisper --break-system-packages"""
import sys, json, subprocess, os
src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '_words.json'
wav = '/tmp/_tw.wav'
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',src,'-ar','16000','-ac','1',wav], check=True)
from faster_whisper import WhisperModel
m = WhisperModel('tiny.en', device='cpu', compute_type='int8')
segs, _ = m.transcribe(wav, word_timestamps=True)
words = [{'w': w.word.strip(), 's': round(w.start,2), 'e': round(w.end,2)} for s in segs for w in s.words]
json.dump(words, open(out,'w'))
print(len(words), 'words ->', out)
print(' '.join(f"{w['w']}[{w['s']}]" for w in words))
