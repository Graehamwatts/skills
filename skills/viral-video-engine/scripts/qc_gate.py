import subprocess, sys, json, re
F=sys.argv[1]
print('=== QC GATE:',F)
d=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',F],capture_output=True,text=True).stdout.strip())
print('duration',round(d,2))
# 1. silence gaps
r=subprocess.run(['ffmpeg','-i',F,'-af','silencedetect=noise=-38dB:d=1.0','-f','null','-'],capture_output=True,text=True)
gaps=re.findall(r'silence_start: ([\d.]+)\n.*?silence_duration: ([\d.]+)',r.stderr)
bad=[(float(a),float(b)) for a,b in gaps if float(a) < d-6]  # ignore end-card outro
print('long-silence gaps (excl. outro):', bad if bad else 'NONE')
# 2. transcript
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',F,'-ar','16000','-ac','1','/tmp/qc_a.wav'],check=True)
from faster_whisper import WhisperModel
m=WhisperModel('tiny.en',device='cpu',compute_type='int8')
segs,_=m.transcribe('/tmp/qc_a.wav')
text=' '.join(s.text.strip() for s in segs)
open('/tmp/qc_transcript.txt','w').write(text)
print('transcript tail:', text[-260:])
# 3. red flags in transcript
flags=[w for w in ['demo me','DM I','do you might','[inaudible]'] if w.lower() in text.lower()]
print('garble flags:', flags if flags else 'NONE')
