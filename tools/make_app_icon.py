#!/usr/bin/env python3
"""Generate the Android launcher icon: Zeus' thunderbolt over a temple.

Adaptive icons keep their content inside the middle ~66% of the canvas,
so the artwork is drawn small and centered.

Usage: make_app_icon.py <android-res-dir>
"""
import os
import sys

from PIL import Image, ImageDraw

GOLD_LIGHT = (247, 226, 160)
GOLD = (226, 178, 74)
GOLD_DARK = (150, 104, 26)
MARBLE = (238, 232, 214)
MARBLE_SHADE = (196, 186, 164)
SKY_TOP = (32, 52, 104)
SKY_BOTTOM = (14, 22, 46)

# Foreground canvas; adaptive icons crop to the middle, so keep art inside.
SIZE = 432
SCALE = 4  # supersampling for smooth edges


def background(size):
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y/(size - 1)
        draw.line([(0, y), (size, y)],
                  fill=tuple(round(a + (b - a)*t)
                             for a, b in zip(SKY_TOP, SKY_BOTTOM)))
    return img


def polygon(draw, points, size, fill, outline=None, width=0):
    draw.polygon([(x*size, y*size) for x, y in points],
                 fill=fill, outline=outline, width=width)


def foreground(size):
    s = size*SCALE
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Temple: three columns on a stepped base, behind the bolt.
    base_y, top_y = 0.72, 0.42
    polygon(draw, [(0.28, base_y), (0.72, base_y),
                   (0.70, base_y + 0.05), (0.30, base_y + 0.05)],
            s, MARBLE_SHADE)
    polygon(draw, [(0.25, base_y + 0.05), (0.75, base_y + 0.05),
                   (0.75, base_y + 0.11), (0.25, base_y + 0.11)],
            s, MARBLE)
    for cx in (0.33, 0.50, 0.67):
        polygon(draw, [(cx - 0.035, base_y), (cx + 0.035, base_y),
                       (cx + 0.030, top_y + 0.10), (cx - 0.030, top_y + 0.10)],
                s, MARBLE)
    # Pediment.
    polygon(draw, [(0.26, top_y + 0.10), (0.74, top_y + 0.10),
                   (0.74, top_y + 0.04), (0.26, top_y + 0.04)],
            s, MARBLE_SHADE)
    polygon(draw, [(0.50, top_y - 0.06), (0.78, top_y + 0.04),
                   (0.22, top_y + 0.04)], s, MARBLE)

    # Thunderbolt, drawn twice for a soft outline.
    bolt = [(0.585, 0.10), (0.315, 0.545), (0.470, 0.545),
            (0.395, 0.905), (0.700, 0.455), (0.530, 0.455),
            (0.640, 0.10)]
    polygon(draw, [(x, y) for x, y in bolt], s, GOLD_DARK)
    inner = [((x - 0.5)*0.90 + 0.5, (y - 0.5)*0.94 + 0.5) for x, y in bolt]
    polygon(draw, inner, s, GOLD)
    core = [((x - 0.5)*0.55 + 0.5, (y - 0.5)*0.80 + 0.5) for x, y in bolt]
    polygon(draw, core, s, GOLD_LIGHT)

    return img.resize((size, size), Image.LANCZOS)


def main(res_dir):
    fg = foreground(SIZE)
    bg = background(SIZE)

    os.makedirs(os.path.join(res_dir, 'drawable'), exist_ok=True)
    fg.save(os.path.join(res_dir, 'drawable', 'ic_launcher_foreground.png'))
    bg.save(os.path.join(res_dir, 'drawable', 'ic_launcher_background.png'))

    # Legacy launcher icons: background with the artwork composited on top.
    for folder, px in [('mipmap-mdpi', 48), ('mipmap-hdpi', 72),
                       ('mipmap-xhdpi', 96), ('mipmap-xxhdpi', 144),
                       ('mipmap-xxxhdpi', 192)]:
        legacy = background(px)
        art = fg.resize((px, px), Image.LANCZOS)
        legacy.paste(art, (0, 0), art)
        os.makedirs(os.path.join(res_dir, folder), exist_ok=True)
        legacy.save(os.path.join(res_dir, folder, 'ic_launcher.png'))

    # Play-store sized preview for sharing.
    store = background(512)
    art = fg.resize((512, 512), Image.LANCZOS)
    store.paste(art, (0, 0), art)
    store.save(os.path.join(res_dir, '..', '..', '..', '..',
                            'icon-preview.png'))
    print('ikonlar uretildi:', res_dir)


if __name__ == '__main__':
    main(sys.argv[1])
