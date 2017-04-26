# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import JsonResponse

import xml.sax
import json
import requests
import time

from .utils import *
from .lemmatizer import lemmatize
from elastic_search import elastic_group, elastic_search2
from elasticsearch import Elasticsearch


es = Elasticsearch('166.111.139.15')

# Create your views here.
def esoda_view(request):
    q = request.GET.get('q', '').strip()

    # No query - render index.html
    if not q:
        info = {
            'feedbackList': [
                {
                    'content': u'无产阶级政党的党章是以马克思主义党的学说为指导，结合党的建设的实践而制定的党的生活准则和行为规范。',
                    'user_name': u'潘星宇'
                },
                {
                    'content': u'无产阶级政党的党章是以马克思主义党的学说为指导，结合党的建设的实践而制定的党的生活准则和行为规范。',
                    'user_name': u'潘星宇'
                }
            ],
            'count_of_favorite': 12049,
        }
        return render(request, 'esoda/index.html', info)

    # With query - render result.html
    q = translate_cn(q)
    usageList = []
    for i in range(1, 28):
        usageList.append({
            'content': 'improve ... quality',
            'count': 609
        })

    r = {
        'domain': u'人机交互',
        'count': 222,
        'phrase': [
            'improve quality',
            'standard quality',
            'best quality'
        ],
        'commonColloc': [
            u'quality (主谓)*',
            u'quality (修饰)*',
            u'quality (介词)*'
        ],
        'collocationList': [
            {
                'type': u'quality (主谓)*',
                'label': 'Colloc1',
                'usageList': usageList,
            },
            {
                'type': u'quality (修饰)*',
                'label': 'Colloc2',
                'usageList': usageList,
            },
            {
                'type': u'quality (介词)*',
                'label': 'Colloc3',
                'usageList': usageList
            },
            {
                'type': u'*(修饰) quality',
                'label': 'Colloc4',
                'usageList': usageList
            }
        ]
    }

    qt = q.split()
    if len(qt) == 1:
        syn = list(synonymous(q))
        if len(syn) > 10:
            syn = syn[0:10]
        r['synonymous'] = syn

    suggestion = {
        'relatedList': [
            'high quality',
            'improve quality',
            'ensure quality',
            '*(修饰) quality'
        ],
        'hotList': [
            'interaction',
            'algorithm',
            'application'
        ]
    }

    info = {
        'r': r,
        'q': q,
        'suggestion': suggestion,
    }

    YOUDAO_SEARCH_URL = 'http://dict.youdao.com/jsonapi?dicts={count:1,dicts:[[\"ec\"]]}&q=%s'
    jsonString = requests.get(YOUDAO_SEARCH_URL % q, timeout=10).text
    jsonObj = json.loads(jsonString.encode('utf-8'))

    if jsonObj.has_key('simple') and jsonObj.has_key('ec'):
        dictionary = {
            'word': q,
            'english': jsonObj['simple']['word'][0].get('ukphone',''),
            'american': jsonObj['simple']['word'][0].get('usphone',''),
            'explanationList': []
        }
        for explain in jsonObj['ec']['word'][0]['trs']:
            dictionary['explanationList'].append(explain['tr'][0]['l']['i'][0])
        info['dictionary'] = dictionary

    return render(request, 'esoda/result.html', info)

def sentence_view(request):
    q = request.GET.get('q', '')
    dtype = request.GET.get('dtype', '')
    sr = sentence_query(q, dtype)
    info = {
        'example_number': sr['total'],
        'search_time': sr['time'],
        'exampleList': sr['sentence']
    }
    return render(request, 'esoda/sentence_result.html', info)

class DictHandler( xml.sax.ContentHandler ):
    def __init__(self):
        self.suggest = []
        self.CurNum = 0
        self.CurTag = ''
        self.category = ''

    def startElement(self, tag, attributes):
        self.CurTag = tag
        if tag == 'item':
            self.suggest.append({})

    def endElement(self, tag):
        if tag == 'item':
            self.suggest[self.CurNum]['category'] = self.category
            self.category = ''
            self.CurNum += 1
        self.CurTag = ''

    def characters(self, content):
        if self.CurTag == 'title':
            self.suggest[self.CurNum]['label'] = content
            if content.find(' ') < 0:
                self.category = 'Words'
            else:
                self.category = 'Expressions'
        elif self.CurTag == 'explain':
            self.suggest[self.CurNum]['desc'] = content

YOUDAO_SUGGEST_URL = 'http://dict.youdao.com/suggest?ver=2.0&le=en&num=10&q=%s'
def dict_suggest_view(request):
    q = request.GET.get('term', '')
    r = {}
    try:
        xmlstring = requests.get(YOUDAO_SUGGEST_URL % q, timeout=10).text
        parser = xml.sax.make_parser()
        parser.setFeature(xml.sax.handler.feature_namespaces, 0)

        Handler = DictHandler()
        xml.sax.parseString(xmlstring.encode('utf-8'), Handler)
        r['suggest'] = Handler.suggest
    except Exception as e:
        print repr(e)
    return JsonResponse(r)

def guide_view(request):
    info = {
    }
    return render(request, 'esoda/guide.html', info)

def sentence_query(q, dtype):
    if dtype != '0': # Search specific tag
        q = gen_qt(q)
        ref = q.split()
        ll = lemmatize(q)
        d = [{'dt': dtype, 'i1': 0, 'i2': 1}]
    else: # Search user input
        q = translate_cn(q)
        ref = q.split()
        ll = lemmatize(q)
        d = []

    time1 = time.time()
    res = elastic_search2(es, ll, d, ref)
    time2 = time.time()

    sr = {'time': round(time2 - time1, 2), 'total': res['total'], 'sentence': []}
    rlen = len(res['hits'])
    for i in xrange(rlen):
        if i > 50:
            break
        sentence = res['hits'][i]
        sr['sentence'].append({
            'content': sentence['fields']['sentence'][0],
            'source': sentence['_source']['p'] + ' ' + sentence['_source']['c'],
            'heart_number': 129})
    return sr
