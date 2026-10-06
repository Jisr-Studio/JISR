"""Language isolation, source fallbacks, lossless migration and mocked job flows."""
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from languages import LANGUAGES, ACTIVE_LANGUAGE, migrate_segments
import test_http

SAMPLES = {'en':'Purification is half of faith.', 'es':'La purificación es la mitad de la fe.',
           'ur':'پاکیزگی نصف ایمان ہے۔','hi':'पवित्रता ईमान का आधा हिस्सा है।',
           'id':'Bersuci adalah separuh iman.','zh-Hans':'洁净是信仰的一半。','tr':'Temizlik imanın yarısıdır.'}
VERSE = 'بسم الله الرحمن الرحيم'
HADITH = 'الطهور شطر الإيمان'


def segment(language='en'):
    words = [{'text':w,'start':i*.4,'end':i*.4+.3} for i,w in enumerate(HADITH.split())]
    return {'id':'d'*12,'ar':HADITH,'translation':SAMPLES[language], 'start':0,'end':1.1,
            'type':'speech','words':words,'reviewed':False,'target_language':language}


class LanguagePolicyTests(unittest.TestCase):
    def test_each_language_reaches_translation_retry_terms_meaning_and_source_alignment(self):
        for code,info in LANGUAGES.items():
            with self.subTest(language=code):
                token=ACTIVE_LANGUAGE.set(code);prompts=[];attempts=0
                seg=segment(code);seg.update(ar='الاجتهاد علم',translation='',words=[{'text':w,'start':i*.4,'end':i*.4+.3} for i,w in enumerate(['الاجتهاد','علم'])],end=.7)
                words=copy.deepcopy(seg['words'])
                def request(payload,key):
                    nonlocal attempts
                    prompts.append(payload['input']);self.assertIn('TARGET LANGUAGE: '+code,payload['input'])
                    props=payload['schema']['properties'];inputs=json.loads(payload['input'].rsplit('Input: ',1)[1])
                    if 'translation_excerpt' in props:
                        result={'translation_excerpt':SAMPLES[code],'confident':True}
                    elif 'quality_items' in props:
                        result={'quality_items':[{'id':s['id'],'translation':s['translation'],'confident':True,'issues':[]} for s in inputs]}
                    elif 'dictionary' in inputs[0]:
                        result={'items':[{'id':s['id'],'translation':SAMPLES[code]} for s in inputs]}
                    else:
                        attempts+=1
                        result={'items':[{'id':s['id'],'terms':['الاجتهاد'],'parts':[{'first_word':1 if attempts==1 else 0,'last_word':1,'kind':'speech','translation':SAMPLES[code]}]} for s in inputs]}
                    return {'status':'completed','text':json.dumps(result,ensure_ascii=False)}
                try:
                    with patch.object(server,'translation_key',return_value='mock'),patch.object(server,'translation_request',side_effect=request),patch.object(server,'lookup_term',return_value={'term':'الاجتهاد','definition_ar':'تعريف عربي موثق','url':'https://islamic-content.com/dictionary/word/196'}):
                        result=server.translate_segments([seg]);self.assertEqual(result[0]['words'],words)
                        server.check_meaning(result,request,'mock',server.normalize_ar)
                        source={'arabic':HADITH+' والصلاة نور','translation':info['labels']['hadith']+' '+SAMPLES[code]+' '+info['labels']['quran'],
                                'kind':'hadith','translation_language':code,'target_language':code,'translation_status':'sourced','partial':True}
                        aligned=server.prepare_quote_subtitles(HADITH,source)
                        self.assertEqual(aligned['subtitle_translation'],SAMPLES[code])
                        self.assertEqual(aligned['alignment_status'],'matched')
                        self.assertEqual(aligned['translation_language'],code)
                    self.assertEqual(attempts,2);self.assertEqual(len(prompts),5)
                finally: ACTIVE_LANGUAGE.reset(token)

    def test_retranslated_source_refresh_keeps_reference_identity_when_translation_missing(self):
        old=segment();old.update(type='hadith',source={'kind':'hadith','id':'3636','arabic':HADITH,'subtitle_arabic':HADITH,
            'translation':SAMPLES['en'],'subtitle_translation':SAMPLES['en'],'source_name':'HadeethEnc','quotation_mode':'quotation','url':'https://hadeethenc.com/ar/browse/hadith/3636','partial':False})
        token=ACTIVE_LANGUAGE.set('es')
        try:
            new=server.reset_translation([old],'es')[0];new['translation']=SAMPLES['es']
            with patch.object(server,'get_json',side_effect=OSError('Unavailable')):
                server.refresh_reference_translation(new)
            self.assertEqual(new['source']['id'],old['source']['id']);self.assertEqual(new['source']['arabic'],old['source']['arabic'])
            self.assertEqual(new['source']['translation'],'');self.assertEqual(new['source']['translation_language'],'es')
            self.assertEqual(new['translation'],SAMPLES['es']);self.assertEqual(new['translation_origin'],'machine')
            self.assertNotIn('English',json.dumps(new,ensure_ascii=False))
            self.assertTrue(new['source']['reference_preserved'])
        finally: ACTIVE_LANGUAGE.reset(token)

    def test_exact_allowlist_and_directions(self):
        self.assertEqual(set(LANGUAGES),{'en','es','ur','hi','id','zh-Hans','tr'})
        for code,item in LANGUAGES.items():
            self.assertEqual(server.validate_language(code),code)
            self.assertEqual(item['direction'],'rtl' if code=='ur' else 'ltr')
        for code in ('zh','ar','EN',None,7,'en; DROP TABLE projects'):
            with self.assertRaises(ValueError): server.validate_language(code)

    def test_legacy_migration_keeps_edits_approvals_and_unicode_spans(self):
        old=[{'id':'old','ar':'العربية','en':'Human edit 😀','reviewed':True,'translation_origin':'human',
              'type':'quran','source_caption':'My own caption','words':[{'text':'العربية','start':1,'end':2}],
              'source':{'arabic':'العربية','english':'😀Human edit','subtitle_english':'Human edit','english_span':{'start':1,'end':11}}}]
        original=copy.deepcopy(old);new=migrate_segments(old)
        self.assertEqual(old,original)
        self.assertEqual(new[0]['translation'],old[0]['en']);self.assertTrue(new[0]['reviewed'])
        self.assertEqual(new[0]['source']['translation_span'],old[0]['source']['english_span'])
        self.assertEqual(new[0]['source_caption'],old[0]['source_caption'])
        self.assertEqual(new[0]['words'],old[0]['words']);self.assertEqual(new[0]['target_language'],'en')
        self.assertEqual(migrate_segments(new),new)
        self.assertNotIn('en',new[0]);self.assertNotIn('english',new[0]['source'])

    def test_reset_keeps_arabic_and_words_but_never_old_translation_or_span(self):
        old=segment();old.update(reviewed=True,source_caption='English caption',quality_input_hash='old',quality_previous_translation='old')
        old['source']={'kind':'hadith','id':'123','arabic':'المصدر العربي','subtitle_arabic':'المصدر','translation':'English source',
                       'subtitle_translation':'English','translation_span':{'start':0,'end':7},'translation_status':'sourced',
                       'quotation_mode':'paraphrase','subtitle_mode':'source_excerpt','speech_translation':'English draft','url':'https://hadeethenc.com/ar/browse/hadith/123'}
        new=server.reset_translation([old],'ur')[0]
        for key in ('ar','words','start','end','id'): self.assertEqual(new[key],old[key])
        self.assertEqual(new['source']['arabic'],old['source']['arabic'])
        self.assertEqual(new['source']['subtitle_mode'],'source_excerpt')
        self.assertFalse(new['reviewed']);self.assertEqual(new['translation'],'')
        self.assertNotIn('source_caption',new);self.assertNotIn('translation_span',new['source'])
        self.assertNotIn('speech_translation',new['source']);self.assertEqual(new['source']['translation_language'],'ur')
        self.assertTrue(new['source']['translation_refresh_required'])
        self.assertEqual(old['translation'],SAMPLES['en'])

    def test_source_language_ids_and_cache_are_not_interchangeable(self):
        seen=[]
        def get(url):
            seen.append(url)
            return {'ayah_number':1,'translation_text':SAMPLES[server.language_code()]}
        with patch.object(server,'get_json',side_effect=get):
            cache_token=server.ACTIVE_SOURCE_CACHE.set({})
            try:
                for code,item in LANGUAGES.items():
                    token=ACTIVE_LANGUAGE.set(code)
                    try:
                        data=server.fetch_quran_translation(1,1)
                        self.assertEqual(data['translation'],SAMPLES[code])
                        self.assertEqual(data['translation_language'],code)
                        self.assertEqual(data['provider_language_id'],item['quran_language_id'])
                        self.assertEqual(data['translation_status'],'sourced')
                        self.assertIn(f"/translation/{item['quran_book']}/",data['translation_url'])
                        server.fetch_quran_translation(1,1)
                    finally: ACTIVE_LANGUAGE.reset(token)
                self.assertEqual(len(seen),7)
            finally: server.ACTIVE_SOURCE_CACHE.reset(cache_token)

    def test_missing_quran_translation_retains_verified_arabic_without_english_fallback(self):
        seg={**segment('hi'),'ar':VERSE,'candidate':{'kind':'quran','surah':1,'ayah':1}}
        def get(url):
            if '/mushafs/' in url: return {'text':VERSE}
            raise urllib.error.HTTPError(url,404,'Not translated',{},None)
        token=ACTIVE_LANGUAGE.set('hi')
        try:
            with patch.object(server,'get_json',side_effect=get),patch.object(server,'lookup_tafsir',return_value={}):
                self.assertTrue(server.verify_quran(seg))
            self.assertEqual(seg['source']['arabic'],VERSE)
            self.assertEqual(seg['source']['translation'],'')
            self.assertEqual(seg['source']['translation_status'],'unavailable')
            self.assertEqual(seg['source']['translator'],'')
            self.assertEqual(seg['source']['translation_notice'],'لا تتوفر ترجمة موثقة بهذه اللغة')
            self.assertEqual(seg['translation'],SAMPLES['hi']);self.assertEqual(seg['translation_origin'],'machine')
            self.assertIn(LANGUAGES['hi']['labels']['draft'],server.make_srt([seg]))
        finally: ACTIVE_LANGUAGE.reset(token)

    def test_hadith_availability_catalog_prevents_wrong_language_request(self):
        token=ACTIVE_LANGUAGE.set('zh-Hans')
        try:
            with patch.object(server,'get_json') as get:
                result=server.fetch_hadith_translation(3636,{'translations':['ar','en']})
                get.assert_not_called();self.assertEqual(result['translation_status'],'unavailable')
            with patch.object(server,'get_json',return_value={'id':3636,'hadeeth':SAMPLES['zh-Hans'],'translations':['ar','zh']}) as get:
                result=server.fetch_hadith_translation(3636,{'translations':['ar','zh']})
                self.assertIn('language=zh',get.call_args.args[0])
                self.assertEqual(result['translation_language'],'zh-Hans')
                self.assertEqual(result['translation'],SAMPLES['zh-Hans'])
        finally: ACTIVE_LANGUAGE.reset(token)

    def test_partial_chinese_source_selection_counts_characters_not_spaces(self):
        token=ACTIVE_LANGUAGE.set('zh-Hans')
        try:
            source={'arabic':'الطهور شطر الإيمان والصلاة نور','translation':'洁净是信仰的一半，礼拜是光明。',
                    'partial':True,'translation_language':'zh-Hans','translation_status':'sourced'}
            selected=server.select_source_translation(source,HADITH,{'start':0,'end':8})
            self.assertEqual(selected['subtitle_translation'],'洁净是信仰的一半')
            with self.assertRaises(ValueError):server.select_source_translation(source,HADITH,{'start':0,'end':len(source['translation'])})
            with self.assertRaises(ValueError):server.select_source_translation({**source,'translation_language':'en'},HADITH,{'start':0,'end':8})
        finally: ACTIVE_LANGUAGE.reset(token)

    def test_chinese_readability_and_quality_hash_are_language_specific(self):
        seg=segment('zh-Hans');seg['translation']='很'*80
        self.assertTrue(server.speech_cue_too_long(seg))
        server.annotate_readability([seg]);self.assertIn('reading_speed',seg['readability']['issues'])
        self.assertNotEqual(server.quality_input_hash(seg),server.quality_input_hash({**seg,'target_language':'en'}))
        self.assertGreater(len(server.wrap_target(seg['translation'],seg).splitlines()),1)

    def test_multipart_language_is_validated_before_the_file_is_written(self):
        with tempfile.TemporaryDirectory() as temp:
            for code in LANGUAGES:
                body=(f'--BOUND\r\nContent-Disposition: form-data; name="target_language"\r\n\r\n{code}\r\n--BOUND\r\n'
                      'Content-Disposition: form-data; name="video"; filename="v.mp4"\r\nContent-Type: video/mp4\r\n\r\nbytes\r\n--BOUND--\r\n').encode()
                metadata={}
                server.save_video_upload(io.BytesIO(body),len(body),'multipart/form-data; boundary=BOUND',Path(temp),metadata)
                self.assertEqual(metadata['target_language'],code)
            bad=body.replace(b'\r\ntr\r\n',b'\r\nfr\r\n')
            with self.assertRaises(ValueError):server.save_video_upload(io.BytesIO(bad),len(bad),'multipart/form-data; boundary=BOUND',Path(temp),{})


class MultilingualHTTPTests(unittest.TestCase):
    setUp=test_http.ProcessingHTTPTests.setUp
    request=test_http.ProcessingHTTPTests.request

    def insert(self,code='en',segments=None):
        project_id='e'*32;folder=server.DATA/project_id;folder.mkdir(exist_ok=True)
        with server.db() as con:
            con.execute('INSERT INTO projects(id,edit_token,share_token,title,filename,status,duration,segments,target_language,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                        (project_id,'editor','f'*32,'Languages','original.mp4','ready',2,json.dumps(segments or [segment(code)]),code,time.time(),time.time()))
        return project_id

    def test_reopen_legacy_project_migrates_without_losing_human_edits(self):
        old={'id':'d'*12,'ar':'اختبار','en':'Edited English','type':'speech','start':0,'end':1,'reviewed':True,'translation_origin':'human'}
        identity=self.insert(segments=[old])
        for _ in range(2):
            _,raw=self.request('/api/projects/'+identity,token='editor');data=json.loads(raw)
            self.assertEqual(data['target_language'],'en');self.assertEqual(data['segments'][0]['translation'],'Edited English')
            self.assertTrue(data['segments'][0]['reviewed']);self.assertNotIn('en',data['segments'][0])

    def test_retranslation_is_explicit_reuses_transcript_and_invalidates_old_download(self):
        old=segment();old.update(reviewed=True,needs_review=False)
        identity=self.insert(segments=[old]);path='/api/projects/'+identity
        _,ticket_raw=self.request(path+'/export/srt','POST',b'{}','editor');ticket=json.loads(ticket_raw)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request(path+'/retranslate','POST',b'{"target_language":"ur"}','editor')
        self.assertEqual(error.exception.code,409)
        prompts=[]
        def translate(payload,key):
            prompts.append(payload['input']);language=server.language_code()
            inputs=json.loads(payload['input'].rsplit('Input: ',1)[1])
            if 'quality_items' in payload['schema']['properties']:
                return {'status':'completed','text':json.dumps({'quality_items':[{'id':x['id'],'translation':x['translation'],'confident':True,'issues':[]} for x in inputs]})}
            return {'status':'completed','text':json.dumps({'items':[{'id':x['id'],'terms':[], 'parts':[{'first_word':0,'last_word':len(x['words'])-1,'kind':'speech','translation':SAMPLES[language]}]} for x in inputs]},ensure_ascii=False)}
        with patch.object(server,'translation_request',side_effect=translate),patch.object(server,'transcribe',side_effect=AssertionError('Retranscription forbidden')) as asr,patch.object(server,'get_json',side_effect=AssertionError('Unexpected external API')):
            status,_=self.request(path+'/retranslate','POST',b'{"target_language":"ur","confirm":true}','editor')
            self.assertEqual(status,202)
            for _ in range(100):
                row=server.project_row(identity)
                if row['status']!='processing':break
                time.sleep(.01)
            self.assertEqual(row['status'],'ready',row['error']);asr.assert_not_called()
        new=json.loads(row['segments'])[0]
        self.assertEqual(new['translation'],SAMPLES['ur']);self.assertEqual(new['words'],old['words'])
        self.assertEqual((new['start'],new['end']),(old['start'],old['end']));self.assertFalse(new['reviewed'])
        self.assertTrue(all('TARGET LANGUAGE: ur' in x for x in prompts))
        self.assertTrue(list((server.DATA/identity/'translation-history').glob('en-*.json')))
        with self.assertRaises(urllib.error.HTTPError) as error:self.request(ticket['download_url'])
        self.assertEqual(error.exception.code,409)
        with self.assertRaises(urllib.error.HTTPError) as error:self.request(path+'/segments/'+new['id'],'POST',b'{"en":"Wrong language"}','editor')
        self.assertEqual(error.exception.code,400)

    @unittest.skipUnless(server.FFMPEG,'Real FFmpeg export required')
    def test_each_language_round_trip_upload_manual_review_srt_share_preview_and_mp4(self):
        video=server.DATA/'synthetic.mp4'
        subprocess.run([server.FFMPEG,'-v','error','-y','-f','lavfi','-i','color=black:s=320x180:r=25:d=2','-c:v','libx264',str(video)],check=True,capture_output=True)
        for code,info in LANGUAGES.items():
            with self.subTest(language=code):
                boundary='language-http'
                body=(f'--{boundary}\r\nContent-Disposition: form-data; name="target_language"\r\n\r\n{code}\r\n--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="test.mp4"\r\nContent-Type: video/mp4\r\n\r\n'.encode()+video.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
                _,raw=self.request('/api/projects','POST',body,content_type=f'multipart/form-data; boundary={boundary}')
                project=json.loads(raw);identity=project['id'];token=project['edit_token'];base='/api/projects/'+identity
                self.assertEqual(project['target_language'],code)
                self.assertEqual(project['translation_direction'],info['direction'])
                _,raw=self.request(base+'/manual','POST',json.dumps({'segments':[{'start':.1,'end':1.7,'ar':HADITH,'translation':SAMPLES[code]}]}).encode(),'{}'.format(token))
                current=json.loads(raw);seg=current['segments'][0]
                _,preview=self.request(base+'/subtitle/'+seg['id'],token=token)
                _,raw=self.request(base+'/segments/'+seg['id'],'POST',b'{"reviewed":true}',token)
                approved=json.loads(raw);self.assertTrue(approved['publishable'])
                _,raw=self.request(base,token=token);self.assertEqual(json.loads(raw)['target_language'],code)
                _,raw=self.request('/api/share/'+approved['share_url'].split('/')[-1]);self.assertEqual(json.loads(raw)['segments'][0]['translation'],SAMPLES[code])
                _,raw=self.request(base+'/export/srt','POST',b'{}',token);ticket=json.loads(raw)
                self.assertIn(code,ticket['filename']);_,srt=self.request(ticket['download_url']);self.assertIn(SAMPLES[code],srt.decode())
                _,raw=self.request(base+'/export/mp4','POST',b'{}',token);ticket=json.loads(raw);_,output=self.request(ticket['download_url'])
                self.assertGreater(len(output),1000)
                exported=server.DATA/identity/f'translated-{code}.mp4'
                subprocess.run([server.FFMPEG,'-v','error','-i',str(exported),'-f','null','-'],check=True,capture_output=True)
                manifest=json.loads((server.DATA/identity/f'render-manifest-{code}.json').read_text())
                self.assertEqual(manifest['target_language'],code)
                image=next(cue['image'] for cue in manifest['cues'] if cue['start']==.1)
                self.assertEqual((server.DATA/identity/image).read_bytes(),preview)

    def test_stale_edit_cannot_restore_a_previous_language(self):
        identity=self.insert();old=server.project_row(identity)
        server.save_project(identity,target_language='es',segments=json.dumps([segment('es')]))
        self.assertFalse(server.save_edit(identity,expected_updated=old['updated'],expected_language='en',segments=old['segments']))
        self.assertEqual(server.project_row(identity)['target_language'],'es')


if __name__=='__main__': unittest.main()
