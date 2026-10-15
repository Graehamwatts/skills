"""python make_qr.py <out.png> "<data>"   e.g. a Switchy short link, or SMSTO:+16503084727:KEYWORD"""
import sys
import qrcode

out, data = sys.argv[1], sys.argv[2]
q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=16, border=2)
q.add_data(data)
q.make(fit=True)
q.make_image(fill_color="#111111", back_color="#ffffff").save(out)
print("wrote", out, "->", data)
