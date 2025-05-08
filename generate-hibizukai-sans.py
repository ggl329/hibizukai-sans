#! /usr/bin/python3

import argparse
from pathlib import Path

import fontforge

import common


# settings

JA_FONT_BASENAME = 'original/BIZUDGothic/BIZUDPGothic'
EN_FONT_BASENAME = 'original/Inter/Inter'

BUILD_DIR = 'HibizukaiSans'
RELEASE_FAMILYNAME = 'HibizukaiSans'
COPYRIGHT = (
    'Copyright 2022 The BIZ UDGothic Project Authors (https://github.com/googlefonts/morisawa-biz-ud-gothic)\n'
    'Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter)\n'
    'Copyright 2025 ggl329 (https://github.com/ggl329/hibizukai-sans)\n'
)
TRADEMARK = 'BIZ UDGothic is a trademark of Morisawa Inc., Inter UI and Inter is a trademark of rsms.'
MANUFACTURER = 'Morisawa Inc., rsms'
DESIGNER = 'TypeBank Co., Ltd., Rasmus Andersson'
LICENSE = (
    'This Font Software is licensed under the SIL Open Font License, Version 1.1. '
    'This license is available with a FAQ at: https://scripts.sil.org/OFL'
)
LICENSE_URL = 'https://scripts.sil.org/OFL'

EM_ASCENT  = 1782    # BIZ UDPGothic = 1802, Inter = 1638
EM_DESCENT =  266    # BIZ UDPGothic =  246, Inter =  410
FONT_ASCENT  = EM_ASCENT  + 170    # BIZ UDPGothic = 1802, Inter = 1984
FONT_DESCENT = EM_DESCENT + 160    # BIZ UDPGothic =  246, Inter =  494

ITALIC_ANGLE = 9.4


def main() -> None:
    args = parse_arguments()

    if not Path(BUILD_DIR).exists():
        Path(BUILD_DIR).mkdir()

    generate_font(for_bold=(args.style == 'bold' or args.style == 'bold-italic'),
                  for_italic=(args.style == 'italic' or args.style == 'bold-italic'),
                  version=args.version)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f'generates a font "{RELEASE_FAMILYNAME}"')
    parser.add_argument('style', choices=['regular', 'bold', 'italic', 'bold-italic'], help='font style to generate')
    parser.add_argument('version', help='version string')
    return parser.parse_args()


def generate_font(for_bold: bool, for_italic: bool, version: str) -> None:
    ja_font = open_ja_orig_font(for_bold)
    en_font = open_en_orig_font(for_bold, for_italic)

    common.scale_em(en_font, EM_ASCENT, EM_DESCENT)
    common.scale_em(ja_font, EM_ASCENT, EM_DESCENT)

    enable_tnum(en_font)

    common.remove_lookups(ja_font, remove_gsub=True, remove_gpos=False)

    clear_duplicate_glyphs(ja_font, en_font)

    if for_italic:
        common.italicize(ja_font, ITALIC_ANGLE)

    common.merge_fonts(ja_font, en_font)

    edit_meta_data(ja_font, for_bold, for_italic, version)

    release_filename = (
        f'{BUILD_DIR}/{RELEASE_FAMILYNAME}-{common.STYLE_TABLE[(for_bold, for_italic)].replace(" ", "")}.ttf'
    )
    ja_font.generate(release_filename)

    en_font.close()
    ja_font.close()


def open_ja_orig_font(for_bold: bool) -> fontforge.font:
    font = fontforge.open(f'{JA_FONT_BASENAME}-{common.STYLE_TABLE[(for_bold, False)]}.ttf')
    common.select_worth_outputting(font)
    font.unlinkReferences()
    return font


def open_en_orig_font(for_bold: bool, for_italic: bool) -> fontforge.font:
    semi_if_bold = 'Semi' if for_bold else ''
    font = fontforge.open(
        f'{EN_FONT_BASENAME}-{semi_if_bold}{common.STYLE_TABLE[(for_bold, for_italic)].replace(" ", "")}.ttf')
    common.select_worth_outputting(font)
    font.unlinkReferences()
    return font


def enable_tnum(font: fontforge.font) -> None:
    for glyph in font.glyphs():
        possub = glyph.getPosSub('*')
        for e in possub:
            if e[0].startswith("'tnum'") and e[1] == 'Substitution':
                font.selection.select(e[2])
                font.copy()
                font.selection.select(glyph)
                font.paste()
                break


def clear_duplicate_glyphs(font1: fontforge.font, font2: fontforge.font) -> None:
    for glyph2 in font2.glyphs():
        if glyph2.isWorthOutputting() and glyph2.unicode > 0:
            font1.selection.select(('unicode',), glyph2.unicode)
            font1.clear()


def edit_meta_data(font: fontforge.font, for_bold: bool, for_italic: bool, version: str) -> None:
    stylename = common.STYLE_TABLE[(for_bold, for_italic)]

    # PS Names
    font.fontname = f'{RELEASE_FAMILYNAME}-{stylename.replace(" ", "")}'
    font.familyname = RELEASE_FAMILYNAME.replace('-', ' ')
    font.fullname = f'{RELEASE_FAMILYNAME.replace("-", " ")} {stylename.replace(" ", "")}'
    font.version = version
    font.sfntRevision = None
    font.copyright = COPYRIGHT

    # OS/2
    font.os2_weight = 700 if for_bold else 400    # 400 = Regular, 700 = Bold
    font.os2_vendor = 'HBZS'
    if for_bold and for_italic:
        font.os2_stylemap = 0x21
    elif for_bold and not for_italic:
        font.os2_stylemap = 0x20
    elif not for_bold and for_italic:
        font.os2_stylemap = 0x01
    elif not for_bold and not for_italic:
        font.os2_stylemap = 0x40

    font.os2_winascent = FONT_ASCENT
    font.os2_windescent = FONT_DESCENT
    font.os2_typoascent = font.ascent
    font.os2_typodescent = -font.descent
    font.os2_typolinegap = 0
    font.hhea_ascent = FONT_ASCENT
    font.hhea_descent = -FONT_DESCENT
    font.hhea_linegap = 0
    font.os2_capheight = round(font[0x48].boundingBox()[3])
    font.os2_xheight = round(font[0x78].boundingBox()[3])

    font.os2_panose = (
        2,     # Family Kind (2 = Latin: Text and Display)
        11,    # Serifs (11 = normal sans)
        8 if for_bold else 5,    # Weight (5 = Book, 8 = Bold)
        3,     # Proportion (3 = Modern)
        0,
        0,
        0,
        0,
        0,
        0
    )

    # TTF names
    font.sfnt_names = (
        ('English (US)', 'Copyright', ''),    # to be inherited
        ('English (US)', 'Family', ''),    # to be inherited
        ('English (US)', 'SubFamily', stylename),
        ('English (US)', 'UniqueID', f'{version};HBZS;{stylename.replace(" ", "")}'),
        ('English (US)', 'Fullname', ''),    # to be inherited
        ('English (US)', 'Version', f'Version {version}'),
        ('English (US)', 'Trademark', TRADEMARK),
        ('English (US)', 'Manufacturer', MANUFACTURER),
        ('English (US)', 'Designer', DESIGNER),
        ('English (US)', 'Vendor URL', ''),
        ('English (US)', 'Designer URL', ''),
        ('English (US)', 'License', LICENSE),
        ('English (US)', 'License URL', LICENSE_URL),
        ('Japanese', 'Copyright', ''),
        ('Japanese', 'Family', RELEASE_FAMILYNAME),
        ('Japanese', 'SubFamily', stylename),
        ('Japanese', 'Fullname', f'{RELEASE_FAMILYNAME} {stylename.replace(" ", "")}'),
        ('Japanese', 'Version', f'Version {version}'),
    )


if __name__ == '__main__':
    main()
