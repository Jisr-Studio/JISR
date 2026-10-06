Subtitle fonts are bundled for the browser preview and FFmpeg export. Each family
includes its SIL Open Font License in the adjacent `*-OFL.txt` file.

Sources: the official [Google Fonts repository](https://github.com/google/fonts).

| File | Family | Source directory |
| --- | --- | --- |
| plex.ttf | IBM Plex Sans Arabic | [ibmplexsansarabic](https://github.com/google/fonts/tree/main/ofl/ibmplexsansarabic) |
| amiri.ttf | Amiri | [amiri](https://github.com/google/fonts/tree/main/ofl/amiri) |
| cairo.ttf | Cairo | [cairo](https://github.com/google/fonts/tree/main/ofl/cairo) |
| tajawal.ttf | Tajawal | [tajawal](https://github.com/google/fonts/tree/main/ofl/tajawal) |
| noto-sans.ttf | Noto Sans Arabic | [notosansarabic](https://github.com/google/fonts/tree/main/ofl/notosansarabic) |
| noto-naskh.ttf | Noto Naskh Arabic | [notonaskharabic](https://github.com/google/fonts/tree/main/ofl/notonaskharabic) |

Cairo and the two Noto families are static instances at their normal width/slant,
400 weight. The system-font option intentionally uses the host's Arial fallback.


## Multilingual subtitle fonts

| File | Family / use | Official source | License |
|---|---|---|---|
| noto-latin.ttf | Noto Sans — English, Spanish, Indonesian, Turkish and punctuation fallback | [Noto Fonts](https://github.com/notofonts/noto-fonts/tree/main/hinted/ttf/NotoSans) | SIL OFL 1.1; noto-latin-OFL.txt |
| noto-urdu.ttf | Noto Nastaliq Urdu — Urdu shaping | [Noto Fonts](https://github.com/notofonts/noto-fonts/tree/main/hinted/ttf/NotoNastaliqUrdu) | SIL OFL 1.1; noto-urdu-OFL.txt |
| noto-devanagari.ttf | Noto Sans Devanagari — Hindi | [Noto Fonts](https://github.com/notofonts/noto-fonts/tree/main/hinted/ttf/NotoSansDevanagari) | SIL OFL 1.1; noto-devanagari-OFL.txt |
| noto-cjk.otf | Noto Sans CJK SC — Simplified Chinese | [Noto CJK](https://github.com/notofonts/noto-cjk/tree/main/Sans/OTF/SimplifiedChinese) | SIL OFL 1.1; noto-cjk-OFL.txt |

Files are unmodified static Regular fonts. Python/FFmpeg and browser @font-face load these same files. Source fonts and matching license notices were downloaded from the official repositories on October 6, 2026. Chinese is the full SC font (approximately 16 MB) rather than a demo-only subset, so uploaded text has broad glyph coverage. OFL covers the fonts, not religious content or API usage rights.
