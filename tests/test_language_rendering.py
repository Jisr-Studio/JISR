"""Check bundled glyphs, shaping and shared renderer images across scripts."""
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from test_languages import SAMPLES, segment
from languages import LANGUAGES
from subtitle_png import alpha_bounds


def cmap_glyphs(font):
    """Read standard SFNT cmap format 4/12; no runtime font dependency."""
    data=font.read_bytes();u16=lambda offset:struct.unpack_from('>H',data,offset)[0];u32=lambda offset:struct.unpack_from('>I',data,offset)[0]
    table=next(u32(12+i*16+8) for i in range(u16(4)) if data[12+i*16:16+i*16]==b'cmap')
    maps=[]
    for i in range(u16(table+2)):
        pos=table+4+i*8;platform,encoding=u16(pos),u16(pos+2)
        if platform==0 or (platform==3 and encoding in (1,10)):
            maps.append(table+u32(pos+4))
    result=set()
    for pos in maps:
        form=u16(pos)
        if form==12:
            for i in range(u32(pos+12)):
                start,end,glyph=struct.unpack_from('>III',data,pos+16+12*i)
                result.update(range(start+(glyph==0),end+1))
        elif form==4:
            count=u16(pos+6)//2;ends=pos+14;starts=ends+count*2+2;deltas=starts+count*2;ranges=deltas+count*2
            for i in range(count):
                start,end,delta,offset=u16(starts+2*i),u16(ends+2*i),u16(deltas+2*i),u16(ranges+2*i)
                for cp in range(start,min(end,0xfffe)+1):
                    glyph=u16(ranges+2*i+offset+(cp-start)*2) if offset else cp
                    if glyph and ((glyph+delta)&0xffff):result.add(cp)
    return result


class LanguageRenderingTests(unittest.TestCase):
    def test_urdu_srt_uses_rtl_marker_including_latin_publisher_caption(self):
        seg=segment('ur');seg.update(type='hadith',source={'kind':'hadith','source_name':'HadeethEnc','id':'3636','translation_status':'sourced'})
        output=server.make_srt([seg])
        self.assertIn('\u200f'+SAMPLES['ur'],output)
        self.assertIn('\u200fHadeethEnc',output)
        self.assertNotIn('\u200f',server.make_srt([segment('hi')]))
    def test_every_bundled_target_font_covers_examples_and_viewer_labels(self):
        for code,info in LANGUAGES.items():
            with self.subTest(language=code):
                extension='otf' if info['font']=='noto-cjk' else 'ttf'
                font=server.DIST/'fonts'/f"{info['font']}.{extension}"
                glyphs=cmap_glyphs(font) | cmap_glyphs(server.DIST/'fonts/noto-latin.ttf') | cmap_glyphs(server.DIST/'fonts/plex.ttf')
                text=SAMPLES[code]+''.join(info['labels'].values())+info['quran_translator']
                self.assertEqual({c for c in text if not c.isspace() and ord(c) not in glyphs},set())
                license=(server.DIST/'fonts'/f"{info['font']}-OFL.txt").read_text()
                self.assertIn('SIL OPEN FONT LICENSE',license)

    @unittest.skipUnless(server.FFMPEG,'FFmpeg/libass required')
    def test_shaped_bilingual_pngs_are_visible_unclipped_and_language_cached(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(server,'DATA',Path(temp)):
            folder=server.DATA/('a'*32);folder.mkdir()
            images=set()
            for code,info in LANGUAGES.items():
                with self.subTest(language=code):
                    seg=segment(code);seg.update(type='quran',ar='بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
                        source={'kind':'quran','surah':1,'ayah':1,'translation_status':'sourced','translator':info['quran_translator']},translation_origin='source')
                    row={'id':folder.name,'target_language':code}
                    image,fitted=server.subtitle_image(row,seg,{'size':42},640,360)
                    images.add(image.name);bounds=alpha_bounds(image.read_bytes())
                    self.assertIsNotNone(bounds);self.assertGreaterEqual(bounds[0],180)
                    self.assertLessEqual(fitted,42)
                    self.assertEqual(server.subtitle_image(row,seg,{'size':42},640,360)[0],image)
                    ass=image.with_suffix('.ass')
                    self.assertIn(info['font_family'],ass.read_text(encoding='utf-8'))
                    probe=subprocess.run([server.FFMPEG,'-v','info','-f','lavfi','-i','color=black:s=640x360',
                        '-vf',f'ass={ass.name}:fontsdir=fonts','-frames:v','1','-f','null','-'],cwd=image.parent,capture_output=True,check=True)
                    stderr=probe.stderr.decode(errors='replace')
                    self.assertNotIn('failed to find any fallback',stderr)
                    self.assertIn(info['font_family'],stderr)
                    blank,_=server.subtitle_image(row,None,{'size':42},640,360)
                    images.add(blank.name)
            self.assertEqual(len(images),14)


if __name__=='__main__':unittest.main()
