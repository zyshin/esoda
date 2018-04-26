# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
import logging
import time
import re
import json
import random

from .utils import *
from common.utils import timeit
from .youdao_query import youdao_suggest, suggest_new
if settings.DEBUG:
    from .youdao_query import youdao_translate_old as youdao_translate
else:
    from .youdao_query import youdao_translate_new as youdao_translate

from .thesaurus import synonyms
from .lemmatizer import lemmatize
from .EsAdaptor import EsAdaptor
from common.models import Comment
from authentication.models import TREE_FIRST, corpus_id2cids, FIELD_NAME


ALL_DEPS = [u'(主谓)', u'(动宾)', u'(修饰)', u'(介词)']
PERP_TOKENS = set(['vs', 're', 'contra', 'concerning', 'neath', 'skyward', 'another', 'near', 'howbeit', 'apropos', 'betwixt', 'alongside', 'amidst', 'outside', 'heavenward', 'notwithstanding', 'withal', 'epithetical', 'anent', 'continuously', 'transversely', 'amongst', 'circa', 'unto', 'aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among', 'around', 'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'besides', 'between', 'beyond', 'but', 'by', 'despite', 'down', 'during', 'except', 'excepting', 'excluding', 'for', 'from', 'in', 'inside', 'into', 'like', 'of', 'off', 'on', 'onto', 'over', 'per', 'since', 'than', 'through', 'to', 'toward', 'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with', 'within', 'without',])
# ALL_DBS = ['dblp', 'doaj', 'bnc', 'arxiv']
DEFAULT_ES_DBS = ['dblp'] # TODO: move into setting.py and .env
DEFAULT_ES_CIDS = ['_all']
logger = logging.getLogger(__name__)

def get_cids(user, r=None):
    dbs, cids = [], []
    if user.is_authenticated:
        corpus_id = user.userprofile.getid()  # user.userprofile.getid() get a list
        dbs, cids = corpus_id2cids(corpus_id)
        # TODO: name = get_name(dbs, cids)
        name = u''
        count = 0
        for i in TREE_FIRST:
            if corpus_id[i] == 1:
                name = name + FIELD_NAME[count] + u', '
            count += 1
        name = name[0:-2]
    else:
        name = u'通用英语'
    if r:
        r['domain'] = name

    dbs = dbs or DEFAULT_ES_DBS
    cids = cids or DEFAULT_ES_CIDS
    return dbs, cids


def get_feedback():
    info = {
        'comments': Comment.get_latest_comments(10),
        'count_of_favorite': 12049,
    }
    return info


@timeit
def esoda_view(request):
    q0 = request.GET.get('q', '').strip()

    # No query - render index.html
    if not q0:
        info = get_feedback()
        return render(request, 'esoda/index.html', info)

    # With query - render result.html
    q = q0
    if has_cn(q0):
        trans = youdao_translate(q0, timeout=3)
        if trans['explanationList']:
            try:
                q = trans['explanationList'][0][trans['explanationList'][0].find(']')+1:].strip()
            except Exception as e:
                logger.exception('Failed to parse youdao_translate result: "%s"', repr(e))

    q, ques, aste = refine_query(q) # ques(aste) is the place of question mark(asterisk)
    qt, ref, poss, dep = lemmatize(q)
    expand = []
    asteList = []
    for i in ques:
        expand.append(i)
    for i in aste:
        asteList.append(i)
    
    r = {
        # 'domain': u'人机交互',
        # 'phrase': [
        #     'improve quality',
        #     'standard quality',
        #     'best quality'
        # ],
        # 'commonColloc': [
        #     u'quality (主谓)*',
        #     u'quality (修饰)*',
        #     u'quality (介词)*'
        # ],
    }

    r['tlen'] = len(qt)
    dbs, cids = get_cids(request.user, r=r)
    cL, cL_index = collocation_list(qt, ref, poss, dep, dbs, cids)
    r['collocationList'] = {'cL': cL, 'index': cL_index}

    suggestion = {
        'relatedList': [
            'high quality',
            'improve quality',
            'ensure quality',
        ],
        'hotList': [
            'interaction',
            'algorithm',
            'application'
        ]
    }

    info = {
        'r': r,
        'q': ' '.join(qt),
        'q0': q0,
        'ref': ' '.join(ref),
        'poss': ' '.join(poss),
        # 'suggestion': suggestion,
        # 'dictionary': trans,
        'cids': cids,
        'expand': json.dumps(expand)
    }

    request.session.save()
    logger.info('%s %s %s %s %s', request.META.get('REMOTE_ADDR', '0.0.0.0'), request.session.session_key, request.user, request, info)
    return render(request, 'esoda/result.html', info)


@timeit
def get_synonyms_dict(t, ref, i, dt, poss, dbs, cids):
    syn_dict = {}
    t_new = t[:]
    ref_new = ref[:]
    if '*' in t:
        syn_dict['*'] = []
        t_new.remove('*')
        ref_new.remove('*')
    for j in xrange(len(t_new)):
        syn_dict[t_new[j]] = []
        for syn in synonyms(t_new[j], pos = poss[j])[:30]:
            lemma = ' '.join(t_new).replace(t_new[j], syn[0])
            reff = ' '.join(ref_new).replace(ref_new[j], syn[0])
            if dt == '0' or len(t_new) == 1:
                cnt = EsAdaptor.count(lemma.split(' '), [], dbs, cids)['hits']['total']
            else:
                d = [{'dt': dt, 'l1': lemma.split(' ')[0], 'l2': lemma.split(' ')[1]}]
                cnt = EsAdaptor.count([], d, dbs, cids)['hits']['total']
            if cnt:
                syn_dict[t_new[j]].append({'ref': reff, 'lemma': lemma, 'content': syn[0], 'count': cnt, 'type': 1, 'weight': syn[1]}) # type 1 for synonyms_word
    return syn_dict


@timeit
def syn_usageList_view(request):
    # info = {
    #    'syn_usage_dict': {'word1':[{'ref': '', 'lemma': '', 'content': '', 'count': 10},……],'word2' ……}
    # }
    t = request.GET.get('t', '').split()
    ref = request.GET.get('ref', '').split()
    expand = request.GET.get('expand', '[]')
    expand = json.loads(expand)
    if not ref:
        ref = t
    i = int(request.GET.get('i', '0'))
    dt = request.GET.get('dt', '0')
    dbs, cids = get_cids(request.user)
    poss = request.GET.get('pos', '').split()
    usage_dict = get_usage_dict(t, ref, i, dt, dbs, cids)
    syn_dict = get_synonyms_dict(t, ref, i, dt, poss, dbs, cids)

    ttcnt = 0
    if dt != '0' and '*' not in t:
        d = [{'dt': dt, 'l1': t[i], 'l2': t[i + 1]}]
        ttcnt = EsAdaptor.count([], d, dbs, cids)['hits']['total']
    else:
        ttcnt = EsAdaptor.count(t, [], dbs, cids)['hits']['total']

    t_list, star = star2collocation(t, dt)
    t_list0 = []
    if expand:
        for i in expand:
            t_list0.append(t_list[i])
        t_list = t_list0
    info = {
        't_list': t_list,
        'count': ttcnt,
        'syn_dict': {},
        't_dt': (' '.join(t), dt),
        'ref': ' '.join(ref)
    }

    syn_usage_dict = {}
    count = 0
    for tt in t:
        syn_usage_dict[tt] = sort_syn_usageDict(syn_dict[tt], usage_dict[tt])
        if tt != '*':
            count += 1

    if '*' in t:
        syn_usage_dict[star] = syn_usage_dict['*']
        if usage_dict.get('*'):
            info['ref'] = usage_dict['*'][0]['ref']
            info['count'] = usage_dict['*'][0]['count']

    hint = 0
    for k in t_list:
        for key in syn_usage_dict.keys():
            if k == key:
                if syn_usage_dict[key]:
                    if count != 1 or dt == '0' or k.encode('utf-8') in ['动词', '宾语', '介词', '修饰词', '被修饰词', '主语']:
                        hint += 1

    info['syn_usage_dict'] = refine_dep(syn_usage_dict, t_list, poss)
    info['hint'] = hint
    logger.info('%s %s %s %s %s', request.META.get('REMOTE_ADDR', '0.0.0.0'), request.session.session_key, request.user, request, info)
    return render(request, 'esoda/collocation_result.html', info)


def sentence_view(request):
    t = request.GET.get('t', '').split()
    ref = request.GET.get('ref', '').split()
    if not ref:
        ref = t
    i = int(request.GET.get('i', '0'))
    dt = request.GET.get('dt', '0')
    dep_count = request.GET.get('dep_count', '0')
    dbs, cids = get_cids(request.user)
    if len(t) == 1:
        dt = '0'
    sr = sentence_query(t, ref, i, dt, dbs, cids)
    # for i in xrange(0, len(sr['sentence']), 10):
    #     temp = sr['sentence'][i:i+10]
    #     random.shuffle(temp)
    #     sr['sentence'][i:i+10] = temp
    info = {
        'example_number': len(sr['sentence']),
        'search_time': sr['time'],
        'exampleList': sr['sentence'],
        'similar_sen': abs(min(int(dep_count), 50) - len(sr['sentence']))
    }
    return render(request, 'esoda/sentence_result.html', info)


# def usagelist_view(request):
#     t = request.GET.get('t', '').split()
#     ref = request.GET.get('ref', '').split()
#     if not ref:
#         ref = t
#     i = int(request.GET.get('i', '0'))
#     dt = request.GET.get('dt', '0')
#     dbs, cids = get_cids(request.user)
#     r = {'usageList': get_usage_list(t, ref, i, dt, dbs, cids)}
#     return render(request, 'esoda/collocation_result.html', r)


def dict_suggest_view(request):
    q = request.GET.get('term', '')
    r = {}
    reMatch = re.compile('^[a-zA-Z0-9\s\'\-\.]*$')
    if reMatch.match(q):
        r = suggest_new(q)
    else:
        r = youdao_suggest(q)
    return JsonResponse(r)


@timeit
def get_usage_dict(t, ref, i, dt, dbs, cids):
    usageDict = {}
    nt = list(t)
    for tt in t:
        usageDict[tt] = []
    if dt == '0':
        return usageDict
    del nt[i]
    del nt[i]
    nnt = list(nt)
    nnt.insert(i, '%s %s')
    pat = ' '.join(nnt)

    # if '*' not in t:
    #     d = [{'dt': dt, 'l1': t[i], 'l2': t[i + 1]}]
    #     cnt = EsAdaptor.count(nt, d, dbs, cids)
    #     usageList.append({
    #         'ref': ' '.join(ref),
    #         'lemma': pat % (t[i], t[i + 1]),
    #         'content': pat % (displayed_lemma(ref[i], t[i]), displayed_lemma(ref[i + 1], t[i + 1])),
    #         'count': cnt['hits']['total']
    #     })
    con = ''
    for k in (('*', t[i + 1]), (t[i], '*')):
        if k == ('*', '*'):
            continue
        d = [{'dt': dt, 'l1': k[0], 'l2': k[1]}]
        lst = EsAdaptor.group(nt, d, dbs, cids)
        try:
            ret = []
            for j in lst['aggregations']['d']['d']['d']['buckets']:
                l1 = notstar(d[0]['l1'], j['key'])
                l2 = notstar(d[0]['l2'], j['key'])
                t1 = [l1 if d[0]['l1'] == '*' else displayed_lemma(ref[i], k[0])]
                t2 = [l2 if d[0]['l2'] == '*' else displayed_lemma(ref[i + 1], k[1])]
                if (l1, l2) != (t[i], t[i + 1]):
                    nref = list(ref)
                    if l1 != t[i]:
                        con = l1
                        nref[i] = l1
                    else:
                        con = l2
                        nref[i + 1] = l2
                    ret.append({
                        'ref': ' '.join(nref),
                        'lemma': pat % (l1, l2), # for query
                        'content': con, # for display
                        'count': j['doc_count'],
                        'type': 2 # for usageword
                    })
            if k[0] == '*':
                usageDict[t[i]] = ret
            else:
                usageDict[t[i+1]] = ret
        except Exception:
            logger.exception('In get_usage_list')
    return usageDict


@timeit
def get_collocations(clist, qt, ref, i, dbs, cids):
    t, d = list(qt), (qt[i], qt[i + 1])
    cnt = 0
    del t[i]
    del t[i]
    resList = EsAdaptor.collocation(t, d, dbs, cids)
    nt = list(t)
    t.insert(i, '%s %s %s')
    pat = ' '.join(t)
    for j, p in enumerate(resList):
        if j == 4:
            qt[i], qt[i + 1] = qt[i + 1], qt[i]
        if not p:
            continue
        if '*' in qt:
            dd = []
            cnt = 10 # one word query set a default number of coll
        else:
            dd = [{'dt': j % 4 + 1, 'l1': qt[i], 'l2': qt[i + 1]}]
            cnt = EsAdaptor.count(nt, dd, dbs, cids)['hits']['total']
        flag = qt.index('*') if '*' in qt else -1
        clist.append({
            'type': pat % (qt[i], ALL_DEPS[j % 4], qt[i + 1]),
            'label': 'Colloc%d_%d' % (len(clist), j % 4 + 1),
            't_dt' : (list(qt), str(j % 4 + 1)),
            'count' : cnt,
            'flag': (flag, str(j % 4 + 1))
            # 'usageList': [],
        })


@timeit
def collocation_list(t, ref, poss, dep, dbs, cids):
    # return collocation_list, default_collocation index
    cnt = EsAdaptor.count(t, [], dbs, cids)['hits']['total']
    head = [{'count': cnt, 't_dt': (t, '0'), 'type': ' '.join(t), 'label':  'Colloc0_0', 'title': u'全部结果'}] # all results
    clist = []
    if len(t) >= 3:
        return head, 1
    if len(t) == 1:
        if t[0] in PERP_TOKENS:
            return head, 1
        t.append('*')
        ref.append('*')
    for i in range(len(t) - 1):
        get_collocations(clist, t, ref, i, dbs, cids)
    newlist, flag = get_defaulteColl(head, poss, dep, clist)
    return newlist, flag


@timeit
def sentence_query(t, ref, i, dt, dbs, cids):
    if not t:
        return {'time': 0.00, 'total': 0, 'sentence': []}
    if dt != '0':  # Search specific tag
        d = [{'dt': dt, 'i1': i, 'i2': i + 1}]
    else:  # Search user input
        d = []

    time1 = time.time()
    res = EsAdaptor.search(t, d, ref, dbs, cids, 50)
    time2 = time.time()

    sr = {'time': round(time2 - time1, 2), 'total': res['total'], 'sentence': []}
    rlen = min(50, len(res['hits']) if 'hits' in res else 0)

    papers = set()
    for i in xrange(rlen):
        papers.add(res['hits'][i]['_source']['p'])
    sources = papers_source_str(list(papers))
    for i in xrange(rlen):
        sentence = res['hits'][i]
        sr['sentence'].append({
            'content': cleaned_sentence(sentence['fields']['sentence'][0]),
            'source': sources.get(sentence['_source']['p'], {}),  # paper_source_str(sentence['_source']['p'])
            'heart_number': 129})
    sr = res_refine(sr)
    return sr
