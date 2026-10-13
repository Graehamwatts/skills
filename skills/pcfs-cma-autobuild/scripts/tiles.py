import sys, os
from PIL import Image
HERE = os.getcwd()  # run from the WORK folder; reads shots/<name>.png and writes shots/<name>_<n>.png
name = sys.argv[1]
im = Image.open(os.path.join(HERE, 'shots', name + '.png')).convert('RGB')
w, h = im.size
# trim trailing white
px = im.load()
bottom = h - 1
while bottom > 0 and all(px[x, bottom] == (255, 255, 255) for x in range(0, w, 40)):
    bottom -= 1
print('size', w, h, 'content bottom', bottom)
step = 1500
i = 0
for y in range(0, bottom, step):
    t = im.crop((0, y, w, min(y + step, bottom + 1)))
    t.save(os.path.join(HERE, 'shots', f'{name}_{i}.png'))
    i += 1
print('tiles', i)
