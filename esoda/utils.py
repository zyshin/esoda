# -*- coding: utf-8 -*-
from .paper import mongo_get_objects, DblpPaper
import re
import string
import logging
import difflib
import math

logger = logging.getLogger(__name__)

DEPS_VIEW = {u'(主谓) *': u' + 动词', u'* (主谓)': u'主语 + ', u'(动宾) *': u' + 宾语', u'* (动宾)': u'动词 + ',
    u'(修饰) *': u' + 被修饰词', u'* (修饰)': u'修饰 + ', u'(介词) *': u' + 介词', u'* (介词)': u'介词 + '}
EN_PUNC = """!"#$%&'()+,-./:;<=>@[\]^_`{|}~""" # string.punctuation去掉问号和星号
CH_PUNC = u'《》（）&%￥#@！{}【】'
PUNC = EN_PUNC + CH_PUNC
TRANS_TABLE = dict((ord(c), u' ') for c in PUNC)
pt2pt = {'VB': 'v', 'VBD': 'v', 'VBG': 'v', 'VBN': 'v', 'VBP': 'v', 'VBZ': 'v',
    'IN': 'prep', 'TO': 'prep', 'RB': 'adv', 'RBR': 'adv', 'RBS': 'adv', 'RP': 'adv',
    'JJ': 'adj', 'JJR': 'adj', 'JJS': 'adj', 'NN': 'n', 'NNP': 'n', 'NNPS': 'n', 'NNS': 'n' }
EXCEPT = {u'her': u'she', u'him': u'he', u'his': u'he', u'its': u'its', u'me': u'I', u'others': u'other', u'our': u'we', u'their': u'they', 
    u'them': u'they', u'us': u'we', u'your': u'you', u'yourselves': u'yourselve', u'data': 'datum'}

def refine_dep(dep_dict, t_list, poss):
    # Only return the English word dep
    bad_case = [u'be']
    refined_dep = {}
    if len(dep_dict) == len(poss):
        for x in xrange(len(poss)):
            if poss[x] not in pt2pt:
                dep_dict[t_list[x]] = []

    for key, value in dep_dict.items():
        if key in bad_case:
            dep_dict[key] = []
        else:
            for v in value:
                if not v['content'].isalpha():
                    value.remove(v)
    return dep_dict


def res_refine(res):
    # Delete the sentences that similarity >= 0.7 and length >= 60
    r = []
    if res['sentence']:
        r.append(res['sentence'][0])
        for i in res['sentence']:
            if len(i['content'].split()) < 60 and difflib.SequenceMatcher(None, r[-1]['content'], i['content']).ratio() < 0.7:
                r.append(i)
    res['sentence'] = r
    return res

def get_defaulteColl(head, poss, dep, clist):
    # TODO: Combine dep and count and poss
    flag = 1
    sec_head = []
    newlist = clist[:]
    if len(poss) == 1 and poss[0]!= 'NONE':
        if pt2pt.get(poss[0]) == 'v':
            set1 = [c for c in clist if c['flag'] == (1 ,'2')]
            set2 = [c for c in clist if c['flag'] == (0 ,'1')]
            last = [c for c in clist if (c['flag'] != (0 ,'1') and c['flag'] != (1 ,'2'))]
        elif pt2pt.get(poss[0]) == 'n':
            set1 = [c for c in clist if c['flag'] == (0 ,'3')]
            set2 = [c for c in clist if c['flag'] == (0 ,'2')]
            last = [c for c in clist if (c['flag'] != (0 ,'3') and c['flag'] != (0 ,'2'))]
        elif pt2pt.get(poss[0]) == 'adj':
            set1 = [c for c in clist if c['flag'] == (0 ,'3')]
            set2 = [c for c in clist if c['flag'] == (1 ,'3')]
            last = [c for c in clist if (c['flag'] != (0 ,'3') and c['flag'] != (1 ,'3'))]
        elif pt2pt.get(poss[0]) == 'prep':
            set1 = [c for c in clist if c['flag'] == (0 ,'4')]
            set2 = [c for c in clist if c['flag'] == (1 ,'4')]
            last = [c for c in clist if (c['flag'] != (0 ,'4') and c['flag'] != (1 ,'4'))]
        elif pt2pt.get(poss[0]) == 'adv':
            set1 = [c for c in clist if c['flag'] == (1 ,'3')]
            set2 = [c for c in clist if c['flag'] == (0 ,'3')]
            last = [c for c in clist if (c['flag'] != (1 ,'3') and c['flag'] != (0 ,'3'))]
        else:
            set1, set2, last = [], [], clist[:]
        newlist = set1 + set2 + last

    elif dep != '0':
        flag = 2
        for cl in clist:
            if cl['t_dt'][1] == dep:
                sec_head = [cl]
                clist.remove(cl)
        newlist = sorted(clist, key=lambda k: k['count'], reverse = True)
    newlist = head + sec_head + newlist
    if flag > len(newlist):
        flag = 1
    return newlist, flag


def displayed_lemma(ref, lemma):
    # if lemma in EXCEPT, change the display of lemma
    if ref in EXCEPT.keys():
        return ref
    else:
       return lemma


def refine_query(q):
    # Note the difference between str.translate and unicode.translate
    ques = []
    aste = []
    q = q.replace(u'？', '?')   # 替换中文问号
    q = re.sub('\s+\?', '?', q) # 去掉问号前空格
    q = re.sub('\?+', '?', q)   # 去掉多个问号
    q = re.sub('^\?', '', q)    # 去掉问号开头
    r = q.translate(TRANS_TABLE).strip()
    r = re.sub(' +', ' ', r)
    wList = r.split()
    for i in range(len(wList)):
        if wList[i].endswith('?'):
            ques.append(i)
        elif wList[i].endswith('*'):
            aste.append(i)
    r = re.sub('\?|\*', '', r)
    if r != q:
        logger.info('refine_query: "%s" -> %s', q, r)
    return r, ques, aste


def convert_type2title(rr):
    rr_title = ''
    if '*' in rr:
        rr_title = re.sub('[a-zA-Z1-9]*', '', rr).strip()
        rr_title = rr.replace(rr_title, DEPS_VIEW[rr_title])
    return rr_title if rr_title else rr


def debug_object(o):
    print '<---- object -----'
    print '\n'.join(["%s:%s" % item for item in o.__dict__.items()])
    print '----- object ---->'


def is_cn_char(c):
    return 0x4e00 <= ord(c) < 0x9fa6


def has_cn(s):
    return reduce(lambda x, y: x or y, [is_cn_char(c) for c in s], False)


def notstar(p, q):
    return p if p != '*' else q


def cleaned_sentence(s):
	# eliminate all possibility of bad HTML in sentence to mark as safe
	return s.replace('<', '< ').replace('< strong>', '<strong>').replace('< /strong>', '</strong>')

def generate_source(year, title, authList, conference):
    source = ''
    # assert: should always be this case
    conference += "'" + str(year % 100)
    source += conference + '. '

    if authList:
        nameList = authList[0].split()  # split first author's name
        authorShort = nameList[0][0].upper() + '. ' +nameList[len(nameList) - 1]
        if len(authList) > 1:
            authorShort += ' et. al.'
        else:
            authorShort += '.'
        source += authorShort
    source += ' ' + title
    return source


def gen_source_url(p):
    year = int(p.get('year'))
    title = p.get('title', '')
    authList = p.get('authors', '').split(';')
    conference = p.get('venue', '/').split('/')[-1].upper()
    source = generate_source(year, title, authList, conference)
    return {'source': source, 'url': p['ee']}


def papers_source_str(pids):
    p = mongo_get_objects(DblpPaper, pks=pids)
    if not p:
        return {}
    # TODO: precompute source string and save to $common.uploads
    # venues = [i['venue'] for i in p.values()]
    # v = mongo_get_objects(DblpVenue, pks=venues)

    res = {}
    for i in pids:
        if i in p:
            res[i] = gen_source_url(p[i])
    return res


def sort_syn_usageDict(syn_list, usage_list):
    unique = []
    new_usagelist = []
    for syn in syn_list:
        syn['weight'] = math.log(syn['count']) # syn['weight'] +
        unique.append(syn['content'])
    for usa in usage_list:
        if usa['content'] not in unique:
            usa['weight'] = math.log(usa['count'])
            new_usagelist.append(usa)
    weighted_list = sorted(syn_list + new_usagelist, key=lambda x:x['weight'], reverse = True)
    return weighted_list


def star2collocation(t, dt):
    star2coll_dict = {'1': {'0': u'主语', '1': u'动词'}, '2':{'0': u'动词', '1': u'宾语'},
        '3':{'0': u'修饰词', '1': u'被修饰词'}, '4':{'0': u'介词', '1': u'介词'}}
    star = ''
    if '*' in t:
        i = t.index('*')
        star = star2coll_dict.get(dt).get(str(i))
        t = [star2coll_dict.get(dt).get(str(i)) if tt =='*' else tt for tt in t]
    return t, star
