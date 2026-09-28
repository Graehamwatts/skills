"""Static inline-SVG line charts for CMA trend sections.

Chart.js canvases need JavaScript, so they come up blank in file previews, the Claude app's preview pane and most email
clients. These charts are plain SVG built at report time: they render in any viewer and print sharply to PDF."""


def line_chart(values, labels, color, tick_fmt, label_fmt, ymin, ymax, step, w=940, h=270):
    L, R, T, B = 66, 18, 16, 36
    n = len(values)

    def X(i):
        return L + i * (w - L - R) / (n - 1)

    def Y(v):
        v = min(max(v, ymin), ymax)
        return T + (ymax - v) * (h - T - B) / (ymax - ymin)

    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f'style="width:100%;height:auto;display:block;font-family:Inter,Arial,sans-serif">']
    v = ymin
    while v <= ymax + 1e-9:
        y = Y(v)
        out.append(f'<line x1="{L}" y1="{y:.1f}" x2="{w - R}" y2="{y:.1f}" stroke="#ececec" stroke-width="1"/>')
        out.append(f'<text x="{L - 8}" y="{y + 4:.1f}" font-size="12" fill="#666" text-anchor="end">{tick_fmt(v)}</text>')
        v += step
    for i, lab in enumerate(labels):
        if lab.startswith(("Jan", "Jul")):
            x = X(i)
            out.append(f'<line x1="{x:.1f}" y1="{h - B}" x2="{x:.1f}" y2="{h - B + 4}" stroke="#bbb" stroke-width="1"/>')
            out.append(f'<text x="{x:.1f}" y="{h - 12}" font-size="12" fill="#666" text-anchor="middle">{lab}</text>')
    pts = [(X(i), Y(v)) for i, v in enumerate(values) if v is not None]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    base = Y(ymin)
    out.append(f'<path d="{d} L{pts[-1][0]:.1f},{base:.1f} L{pts[0][0]:.1f},{base:.1f} Z" fill="{color}" fill-opacity="0.08" stroke="none"/>')
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    last = [v for v in values if v is not None][-1]
    lx, ly = pts[-1]
    out.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.5" fill="{color}"/>')
    out.append(f'<text x="{lx - 7:.1f}" y="{ly - 9:.1f}" font-size="12.5" font-weight="700" fill="{color}" text-anchor="end">{label_fmt(last)}</text>')
    out.append("</svg>")
    return "".join(out)
