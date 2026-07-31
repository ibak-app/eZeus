#!/usr/bin/env python3
"""Add the six Turkish glyphs missing from Zeus.ttf.

The font already covers the rest of Turkish (ç ö ü â î and capitals).
The additions are composed from existing outlines:

  ı (U+0131) = i                     (the font's i is already dotless)
  İ (U+0130) = I + period dot above
  ğ (U+011F) = g + breve
  Ğ (U+011E) = G + breve (scaled to fit under the ascender)
  ş (U+015F) = s + comma below (cedilla look-alike)
  Ş (U+015E) = S + comma below

Usage: add_turkish_glyphs.py <in.ttf> <out.ttf>
"""
import sys

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


def bounds(glyphSet, name):
    pen = BoundsPen(glyphSet)
    glyphSet[name].draw(pen)
    return pen.bounds  # (xMin, yMin, xMax, yMax)


def compose(font, newName, baseName, accentName=None, accentTransform=None):
    """Create newName from baseName plus an optionally transformed accent."""
    glyphSet = font.getGlyphSet()
    pen = TTGlyphPen(glyphSet)
    glyphSet[baseName].draw(pen)
    if accentName is not None:
        glyphSet[accentName].draw(TransformPen(pen, accentTransform))
    font['glyf'][newName] = pen.glyph()
    font['hmtx'][newName] = font['hmtx'][baseName]


def accent_above(glyphSet, baseName, accentName, gap, scale=1.0, maxTop=None):
    """Transform placing accent centered above the base with a gap."""
    bx0, _, bx1, bTop = bounds(glyphSet, baseName)
    ax0, aBottom, ax1, aTop = bounds(glyphSet, accentName)
    if maxTop is not None:
        # Shrink until the accent fits under maxTop.
        while bTop + gap + (aTop - aBottom)*scale > maxTop and scale > 0.3:
            scale -= 0.05
    dx = (bx0 + bx1)/2 - (ax0 + ax1)/2*scale
    dy = bTop + gap - aBottom*scale
    return Transform(scale, 0, 0, scale, dx, dy)


def accent_below(glyphSet, baseName, accentName, gap, scale, minBottom):
    """Transform placing accent centered below the base with a gap."""
    bx0, bBottom, bx1, _ = bounds(glyphSet, baseName)
    ax0, aBottom, ax1, aTop = bounds(glyphSet, accentName)
    while bBottom - gap - (aTop - aBottom)*scale < minBottom and scale > 0.2:
        scale -= 0.05
    dx = (bx0 + bx1)/2 - (ax0 + ax1)/2*scale
    dy = bBottom - gap - aTop*scale
    return Transform(scale, 0, 0, scale, dx, dy)


def main(src, dst):
    font = TTFont(src)
    glyphSet = font.getGlyphSet()
    ascent = font['hhea'].ascent    # 905
    descent = font['hhea'].descent  # -199

    order = font.getGlyphOrder()
    additions = {
        'idotless': 0x0131,
        'Idotaccent': 0x0130,
        'gbreve': 0x011F,
        'Gbreve': 0x011E,
        'scedilla': 0x015F,
        'Scedilla': 0x015E,
    }
    font.setGlyphOrder(order + list(additions))

    # ı — plain copy of the dotless i.
    compose(font, 'idotless', 'i')
    # İ — I with the period reused as a dot above.
    compose(font, 'Idotaccent', 'I', 'period',
            accent_above(glyphSet, 'I', 'period', gap=40, maxTop=ascent))
    # ğ Ğ — breve above, scaled down for the capital.
    compose(font, 'gbreve', 'g', 'breve',
            accent_above(glyphSet, 'g', 'breve', gap=20, maxTop=ascent))
    compose(font, 'Gbreve', 'G', 'breve',
            accent_above(glyphSet, 'G', 'breve', gap=5, maxTop=ascent))
    # ş Ş — comma below as a cedilla stand-in.
    compose(font, 'scedilla', 's', 'comma',
            accent_below(glyphSet, 's', 'comma', gap=5, scale=0.55,
                         minBottom=descent))
    compose(font, 'Scedilla', 'S', 'comma',
            accent_below(glyphSet, 'S', 'comma', gap=5, scale=0.55,
                         minBottom=descent))

    for table in font['cmap'].tables:
        if table.isUnicode():
            for name, code in additions.items():
                table.cmap[code] = name

    font.save(dst)
    print(f"saved {dst}")

    check = TTFont(dst)
    cmap = check.getBestCmap()
    missing = [chr(c) for c in additions.values() if c not in cmap]
    print("eksik:", missing if missing else "yok — Türkçe tam ✓")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
