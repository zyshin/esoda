# -*- coding: utf-8 -*-
from common.mongodb import MONGODB
from .paper import mongo_get_object, mongo_get_objects, mongo_get_object_or_404, DblpPaper, UploadRecord
import requests
import json

CORPUS2ID = {"0": [{"i": "bnc", "d": "bnc"}], "1": [{"i": "conf/IEEEpact", "d": "dblp"}, {"i": "conf/asplos", "d": "dblp"}, {"i": "conf/cgo", "d": "dblp"}, {"i": "conf/cloud", "d": "dblp"}, {"i": "conf/cnhpca", "d": "dblp"}, {"i": "conf/codes", "d": "dblp"}, {"i": "conf/date", "d": "dblp"}, {"i": "conf/eurodac", "d": "dblp"}, {"i": "conf/fast", "d": "dblp"}, {"i": "conf/fpga", "d": "dblp"}, {"i": "conf/hipeac", "d": "dblp"}, {"i": "conf/hpdc", "d": "dblp"}, {"i": "conf/iccad", "d": "dblp"}, {"i": "conf/iccd", "d": "dblp"}, {"i": "conf/icdcs", "d": "dblp"}, {"i": "conf/icpp", "d": "dblp"}, {"i": "conf/ics", "d": "dblp"}, {"i": "conf/ipps", "d": "dblp"}, {"i": "conf/isca", "d": "dblp"}, {"i": "conf/itc", "d": "dblp"}, {"i": "conf/lisa", "d": "dblp"}, {"i": "conf/mss", "d": "dblp"}, {"i": "conf/parco", "d": "dblp"}, {"i": "conf/performance", "d": "dblp"}, {"i": "conf/podc", "d": "dblp"}, {"i": "conf/ppopp", "d": "dblp"}, {"i": "conf/rtas", "d": "dblp"}, {"i": "conf/sc", "d": "dblp"}, {"i": "conf/sigmetrics", "d": "dblp"}, {"i": "conf/spaa", "d": "dblp"}, {"i": "conf/usenix", "d": "dblp"}, {"i": "conf/vee", "d": "dblp"}, {"i": "journals/jpdc", "d": "dblp"}, {"i": "journals/jsa", "d": "dblp"}, {"i": "journals/pe", "d": "dblp"}, {"i": "journals/taas", "d": "dblp"}, {"i": "journals/taco", "d": "dblp"}, {"i": "journals/tc", "d": "dblp"}, {"i": "journals/tcad", "d": "dblp"}, {"i": "journals/tecs", "d": "dblp"}, {"i": "journals/tocs", "d": "dblp"}, {"i": "journals/todaes", "d": "dblp"}, {"i": "journals/tos", "d": "dblp"}, {"i": "journals/tpds", "d": "dblp"}, {"i": "journals/trets", "d": "dblp"}, {"i": "journals/tvlsi", "d": "dblp"}, {"i": "journals/micro", "d": "dblp"}, {"i": "conf/eurosys", "d": "dblp"}], "2": [{"i": "conf/conext", "d": "dblp"}, {"i": "conf/icnp", "d": "dblp"}, {"i": "conf/imc", "d": "dblp"}, {"i": "conf/infocom", "d": "dblp"}, {"i": "conf/ipsn", "d": "dblp"}, {"i": "conf/iwqos", "d": "dblp"}, {"i": "conf/mobicom", "d": "dblp"}, {"i": "conf/mobihoc", "d": "dblp"}, {"i": "conf/mobisys", "d": "dblp"}, {"i": "conf/nossdav", "d": "dblp"}, {"i": "conf/nsdi", "d": "dblp"}, {"i": "conf/secon", "d": "dblp"}, {"i": "conf/sensys", "d": "dblp"}, {"i": "conf/sigcomm", "d": "dblp"}, {"i": "journals/cn", "d": "dblp"}, {"i": "journals/jsac", "d": "dblp"}, {"i": "journals/tcom", "d": "dblp"}, {"i": "journals/tmc", "d": "dblp"}, {"i": "journals/toit", "d": "dblp"}, {"i": "journals/ton", "d": "dblp"}, {"i": "journals/tosn", "d": "dblp"}, {"i": "journals/twc", "d": "dblp"}], "3": [{"i": "conf/acsac", "d": "dblp"}, {"i": "conf/asiacrypt", "d": "dblp"}, {"i": "conf/ccs", "d": "dblp"}, {"i": "conf/ches", "d": "dblp"}, {"i": "conf/crypto", "d": "dblp"}, {"i": "conf/csfw", "d": "dblp"}, {"i": "conf/dsn", "d": "dblp"}, {"i": "conf/esorics", "d": "dblp"}, {"i": "conf/eurocrypt", "d": "dblp"}, {"i": "conf/fse", "d": "dblp"}, {"i": "conf/ndss", "d": "dblp"}, {"i": "conf/pkc", "d": "dblp"}, {"i": "conf/raid", "d": "dblp"}, {"i": "conf/sp", "d": "dblp"}, {"i": "conf/srds", "d": "dblp"}, {"i": "conf/tcc", "d": "dblp"}, {"i": "conf/uss", "d": "dblp"}, {"i": "journals/compsec", "d": "dblp"}, {"i": "journals/dcc", "d": "dblp"}, {"i": "journals/jcs", "d": "dblp"}, {"i": "journals/joc", "d": "dblp"}, {"i": "journals/tdsc", "d": "dblp"}, {"i": "journals/tifs", "d": "dblp"}, {"i": "journals/tissec", "d": "dblp"}], "4": [{"i": "conf/caise", "d": "dblp"}, {"i": "conf/cp", "d": "dblp"}, {"i": "conf/ecoop", "d": "dblp"}, {"i": "conf/esem", "d": "dblp"}, {"i": "conf/etaps", "d": "dblp"}, {"i": "conf/fm", "d": "dblp"}, {"i": "conf/hotos", "d": "dblp"}, {"i": "conf/icfp", "d": "dblp"}, {"i": "conf/icse", "d": "dblp"}, {"i": "conf/icsm", "d": "dblp"}, {"i": "conf/icsoc", "d": "dblp"}, {"i": "conf/icws", "d": "dblp"}, {"i": "conf/issre", "d": "dblp"}, {"i": "conf/issta", "d": "dblp"}, {"i": "conf/iwpc", "d": "dblp"}, {"i": "conf/kbse", "d": "dblp"}, {"i": "conf/lctrts", "d": "dblp"}, {"i": "conf/middleware", "d": "dblp"}, {"i": "conf/models", "d": "dblp"}, {"i": "conf/oopsla", "d": "dblp"}, {"i": "conf/osdi", "d": "dblp"}, {"i": "conf/pldi", "d": "dblp"}, {"i": "conf/popl", "d": "dblp"}, {"i": "conf/re", "d": "dblp"}, {"i": "conf/sas", "d": "dblp"}, {"i": "conf/sigsoft", "d": "dblp"}, {"i": "conf/sosp", "d": "dblp"}, {"i": "conf/vmcai", "d": "dblp"}, {"i": "conf/wcre", "d": "dblp"}, {"i": "journals/ase", "d": "dblp"}, {"i": "journals/ese", "d": "dblp"}, {"i": "journals/iee", "d": "dblp"}, {"i": "journals/infsof", "d": "dblp"}, {"i": "journals/jfp", "d": "dblp"}, {"i": "journals/jss", "d": "dblp"}, {"i": "journals/re", "d": "dblp"}, {"i": "journals/scp", "d": "dblp"}, {"i": "journals/smr", "d": "dblp"}, {"i": "journals/sosym", "d": "dblp"}, {"i": "journals/spe", "d": "dblp"}, {"i": "journals/stvr", "d": "dblp"}, {"i": "journals/toplas", "d": "dblp"}, {"i": "journals/tosem", "d": "dblp"}, {"i": "journals/tsc", "d": "dblp"}, {"i": "journals/tse", "d": "dblp"}], "5": [{"i": "conf/cidr", "d": "dblp"}, {"i": "conf/cikm", "d": "dblp"}, {"i": "conf/dasfaa", "d": "dblp"}, {"i": "conf/ecml", "d": "dblp"}, {"i": "conf/edbt", "d": "dblp"}, {"i": "conf/icde", "d": "dblp"}, {"i": "conf/icdm", "d": "dblp"}, {"i": "conf/icdt", "d": "dblp"}, {"i": "conf/kdd", "d": "dblp"}, {"i": "conf/pods", "d": "dblp"}, {"i": "conf/sdm", "d": "dblp"}, {"i": "conf/semweb", "d": "dblp"}, {"i": "conf/sigir", "d": "dblp"}, {"i": "conf/sigmod", "d": "dblp"}, {"i": "conf/vldb", "d": "dblp"}, {"i": "conf/wsdm", "d": "dblp"}, {"i": "journals/aei", "d": "dblp"}, {"i": "journals/datamine", "d": "dblp"}, {"i": "journals/dke", "d": "dblp"}, {"i": "journals/ejis", "d": "dblp"}, {"i": "journals/geoinformatica", "d": "dblp"}, {"i": "journals/ipm", "d": "dblp"}, {"i": "journals/is", "d": "dblp"}, {"i": "journals/isci", "d": "dblp"}, {"i": "journals/jasis", "d": "dblp"}, {"i": "journals/kais", "d": "dblp"}, {"i": "journals/tkdd", "d": "dblp"}, {"i": "journals/tkde", "d": "dblp"}, {"i": "journals/tods", "d": "dblp"}, {"i": "journals/tois", "d": "dblp"}, {"i": "journals/tweb", "d": "dblp"}, {"i": "journals/vldb", "d": "dblp"}, {"i": "journals/ws", "d": "dblp"}], "6": [{"i": "conf/cade", "d": "dblp"}, {"i": "conf/cav", "d": "dblp"}, {"i": "conf/coco", "d": "dblp"}, {"i": "conf/compgeom", "d": "dblp"}, {"i": "conf/concur", "d": "dblp"}, {"i": "conf/esa", "d": "dblp"}, {"i": "conf/focs", "d": "dblp"}, {"i": "conf/hybrid", "d": "dblp"}, {"i": "conf/icalp", "d": "dblp"}, {"i": "conf/lics", "d": "dblp"}, {"i": "conf/soda", "d": "dblp"}, {"i": "conf/stoc", "d": "dblp"}, {"i": "journals/algorithmica", "d": "dblp"}, {"i": "journals/cc", "d": "dblp"}, {"i": "journals/fac", "d": "dblp"}, {"i": "journals/fmsd", "d": "dblp"}, {"i": "journals/iandc", "d": "dblp"}, {"i": "journals/informs", "d": "dblp"}, {"i": "journals/jcss", "d": "dblp"}, {"i": "journals/jgo", "d": "dblp"}, {"i": "journals/jsc", "d": "dblp"}, {"i": "journals/mscs", "d": "dblp"}, {"i": "journals/siamcomp", "d": "dblp"}, {"i": "journals/talg", "d": "dblp"}, {"i": "journals/tcs", "d": "dblp"}, {"i": "journals/tit", "d": "dblp"}, {"i": "journals/tocl", "d": "dblp"}, {"i": "journals/toms", "d": "dblp"}], "7": [{"i": "conf/dcc", "d": "dblp"}, {"i": "conf/eurographics", "d": "dblp"}, {"i": "conf/icassp", "d": "dblp"}, {"i": "conf/icmcs", "d": "dblp"}, {"i": "conf/mir", "d": "dblp"}, {"i": "conf/mm", "d": "dblp"}, {"i": "conf/pg", "d": "dblp"}, {"i": "conf/rt", "d": "dblp"}, {"i": "conf/sca", "d": "dblp"}, {"i": "conf/sgp", "d": "dblp"}, {"i": "conf/si3d", "d": "dblp"}, {"i": "conf/siggraph", "d": "dblp"}, {"i": "conf/sma", "d": "dblp"}, {"i": "conf/vissym", "d": "dblp"}, {"i": "conf/visualization", "d": "dblp"}, {"i": "journals/cad", "d": "dblp"}, {"i": "journals/cagd", "d": "dblp"}, {"i": "journals/cgf", "d": "dblp"}, {"i": "journals/cvgip", "d": "dblp"}, {"i": "journals/siamis", "d": "dblp"}, {"i": "journals/speech", "d": "dblp"}, {"i": "journals/tcsv", "d": "dblp"}, {"i": "journals/tip", "d": "dblp"}, {"i": "journals/tmm", "d": "dblp"}, {"i": "journals/tog", "d": "dblp"}, {"i": "journals/tomccap", "d": "dblp"}, {"i": "journals/tvcg", "d": "dblp"}, {"i": "conf/vr", "d": "dblp"}], "8": [{"i": "conf/aaai", "d": "dblp"}, {"i": "conf/acl", "d": "dblp"}, {"i": "conf/aips", "d": "dblp"}, {"i": "conf/atal", "d": "dblp"}, {"i": "conf/coling", "d": "dblp"}, {"i": "conf/colt", "d": "dblp"}, {"i": "conf/cvpr", "d": "dblp"}, {"i": "conf/ecai", "d": "dblp"}, {"i": "conf/eccv", "d": "dblp"}, {"i": "conf/emnlp", "d": "dblp"}, {"i": "conf/iccbr", "d": "dblp"}, {"i": "conf/iccv", "d": "dblp"}, {"i": "conf/icml", "d": "dblp"}, {"i": "conf/icra", "d": "dblp"}, {"i": "conf/ijcai", "d": "dblp"}, {"i": "conf/kr", "d": "dblp"}, {"i": "conf/nips", "d": "dblp"}, {"i": "conf/ppsn", "d": "dblp"}, {"i": "conf/uai", "d": "dblp"}, {"i": "journals/aamas", "d": "dblp"}, {"i": "journals/ai", "d": "dblp"}, {"i": "journals/coling", "d": "dblp"}, {"i": "journals/cviu", "d": "dblp"}, {"i": "journals/ec", "d": "dblp"}, {"i": "journals/ijar", "d": "dblp"}, {"i": "journals/ijcv", "d": "dblp"}, {"i": "journals/jair", "d": "dblp"}, {"i": "journals/jar", "d": "dblp"}, {"i": "journals/jmlr", "d": "dblp"}, {"i": "journals/ml", "d": "dblp"}, {"i": "journals/neco", "d": "dblp"}, {"i": "journals/nn", "d": "dblp"}, {"i": "journals/pami", "d": "dblp"}, {"i": "journals/taffco", "d": "dblp"}, {"i": "journals/tap", "d": "dblp"}, {"i": "journals/taslp", "d": "dblp"}, {"i": "journals/tcyb", "d": "dblp"}, {"i": "journals/tec", "d": "dblp"}, {"i": "journals/tfs", "d": "dblp"}, {"i": "journals/tnn", "d": "dblp"}, {"i": "journals/tslp", "d": "dblp"}, {"i": "conf/par", "d": "dblp"}], "9": [{"i": "conf/chi", "d": "dblp"}, {"i": "conf/cscw", "d": "dblp"}, {"i": "conf/ecscw", "d": "dblp"}, {"i": "conf/group", "d": "dblp"}, {"i": "conf/huc", "d": "dblp"}, {"i": "conf/iui", "d": "dblp"}, {"i": "conf/mhci", "d": "dblp"}, {"i": "conf/percom", "d": "dblp"}, {"i": "conf/tabletop", "d": "dblp"}, {"i": "conf/uist", "d": "dblp"}, {"i": "journals/cscw", "d": "dblp"}, {"i": "journals/hhci", "d": "dblp"}, {"i": "journals/ijhci", "d": "dblp"}, {"i": "journals/ijmms", "d": "dblp"}, {"i": "journals/iwc", "d": "dblp"}, {"i": "journals/thms", "d": "dblp"}, {"i": "journals/tochi", "d": "dblp"}, {"i": "journals/umuai", "d": "dblp"}], "10": [{"i": "conf/bibm", "d": "dblp"}, {"i": "conf/cogsci", "d": "dblp"}, {"i": "conf/emsoft", "d": "dblp"}, {"i": "conf/recomb", "d": "dblp"}, {"i": "conf/rtss", "d": "dblp"}, {"i": "conf/www", "d": "dblp"}, {"i": "journals/bib", "d": "dblp"}, {"i": "journals/bioinformatics", "d": "dblp"}, {"i": "journals/chinaf", "d": "dblp"}, {"i": "journals/cj", "d": "dblp"}, {"i": "journals/jacm", "d": "dblp"}, {"i": "journals/jamia", "d": "dblp"}, {"i": "journals/jcst", "d": "dblp"}, {"i": "journals/pieee", "d": "dblp"}, {"i": "journals/ploscb", "d": "dblp"}, {"i": "journals/tase", "d": "dblp"}, {"i": "journals/tgrs", "d": "dblp"}, {"i": "journals/tits", "d": "dblp"}, {"i": "journals/tmi", "d": "dblp"}, {"i": "journals/trob", "d": "dblp"}, {"i": "journals/wwwj", "d": "dblp"}]}

CORPUS2ID["11"] = [{"i": "_all", "d": "dblp"}]

def debug_object(o):
    print '<---- object -----'
    print '\n'.join(["%s:%s" % item for item in o.__dict__.items()])
    print '----- object ---->'


def is_cn_char(c):
    return 0x4e00 <= ord(c) < 0x9fa6


def is_cn(s):
    return reduce(lambda x, y: x and y, [is_cn_char(c) for c in s], True)

def has_cn(s):
    return reduce(lambda x, y: x or y, [is_cn_char(c) for c in s], False)


def translate(cn):
    url = u'http://fanyi.youdao.com/openapi.do?keyfrom=ESLWriter&key=205873295&type=data&doctype=json&version=1.2&only=dict&q=' + cn
    l = ''
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            o = r.json()
            if o['errorCode'] == 0 and 'basic' in o and 'explains' in o['basic']:
                s = o['basic']['explains'][0]
                l = s[s.find(']') + 1:].strip()
    except Exception as e:
        print e
    return l


def corpus_id2cids(corpus_id):
    if corpus_id in CORPUS2ID:
        return [c['i'].replace('/', '_') for c in CORPUS2ID[corpus_id]]
    return [c['_id'].replace('/', '_') for c in MONGODB['dblp']['venues'].find({'field': corpus_id})]


def translate_cn(q):
    tokens = q.split()
    lent = len(tokens)
    qtt = []
    for i in xrange(lent):
        t = tokens[i]
        if is_cn(t):
            t = translate(t.strip('?'))
            # if not t:
            #     no translation for Chinese keyword
        qtt.append(t)
    st = ' '
    return st.join(qtt)


def notstar(p, q):
    return p if p != '*' else q


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


def paper_source_str(pid):
    s = {}
    p = mongo_get_object(DblpPaper, pk=pid)
    if not p:
        p = mongo_get_object_or_404(UploadRecord, pk=pid)
        s['source'] = 'Uploaded file: ' + p['title']
        return s
    # TODO: precompute source string and save to $common.uploads
    # v = mongo_get_object(DblpVenue, pk=p['venue'])
    return gen_source_url(p)


def papers_source_str(pids):
    p = mongo_get_objects(DblpPaper, pks=pids)
    if not p:
        return {}
    # TODO: precompute source string and save to $common.uploads
    # venues = [i['venue'] for i in p.values()]
    # v = mongo_get_objects(DblpVenue, pks=venues)

    res = {}
    for i in pids:
        res[i] = gen_source_url(p[i])
    return res
