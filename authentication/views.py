# This Python file uses the following encoding: utf-8
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.http import JsonResponse
import json
from .models import UserProfile, CORPUS, SECOND_LEVEL_FIELD, FIELD_NAME


# Create your views here.

# Views for profile urls
def domain_view(request):
    user = request.user
    if request.method == 'POST':
        corpus_ids = UserProfile.EMPTY_CIDS[:]
        cids = request.POST.getlist('ids')
        for i in cids:
            corpus_ids[int(i)] = 1
        if user.is_authenticated():
            if cids:
                user.userprofile.setid(corpus_ids)
                messages.success(request, _(u'保存成功'))
            else:
                messages.error(request, _(u'请至少选择一个领域'))
        else:
            messages.error(request, _(u'请先登录'))
    else:
        corpus_ids = user.userprofile.getid() if user.is_authenticated() else UserProfile.DEFAULT_CIDS[:]
    node_tree = tree(corpus_ids)
    return render(request, "profile/domain_select.html", {'menu_index': 1, 'profileTab': 'domain','corpus': node_tree})

@login_required
def search_domain_tree_view(request):
    result = []
    expand = []
    big = []
    target = request.GET['target']
    if target == "":
        return JsonResponse({"expand": expand, "result": result, "big": big}, safe=False)
    user = User.objects.get(id=request.user.pk)
    corpus_id = user.userprofile.getid()
    node_tree = tree(corpus_id)
    for k in node_tree:
        for i in k["nodes"]:
            for j in i["nodes"]:
                if target.lower() in j["text"].lower():
                    result.append(j["id"])
                    if k["level"] == 3:
                        if not i["id"] in expand:
                            expand.append(i["id"])
                    if not k["id"] in big:
                        big.append(k["id"])
    return JsonResponse({"expand": expand, "result": result, "big": big}, safe=False)


def personal_view(request):
    info = {
        'profileTab': 'personal'
    }
    return render(request, 'profile/personal.html', info)


def favorites_view(request):
    exampleList = []
    for i in range(1, 51):
        exampleList.append({
            'content': 'The crucial <strong>quality</strong> of this active assimilation was that it guaranteed a certain depth in the individual meteorologist\'s interpretation of the information.',
            'source': 'UIST\'07. M. Morris et. al.SearchTogether: an interface for collaborative web search.',
            'heart_number': 129,
        })

    info = {
        'example_number': 50,
        'search_time': 0.1,
        'exampleList': exampleList,
        'profileTab': 'favorites'
    }
    return render(request, 'profile/favorites.html', info)


def get_dept_tree(corpus_id):
    display_tree = []
    c_id = 0
    a_id = 0
    for k in range(len(FIELD_NAME)):
        node0 = TreeNode()
        node0.id = c_id
        c_id += 1
        node0.text = FIELD_NAME[k]
        field_tree = []
        if len(SECOND_LEVEL_FIELD[k]) > 1:
            node0.level = 3
        for i in range(len(SECOND_LEVEL_FIELD[k])):
            node = TreeNode()
            node.id = c_id
            node.text = SECOND_LEVEL_FIELD[k][i]
            c_id += 1
            children = CORPUS[str(a_id)]
            a_id += 1
            for i in children:
                node1 = TreeNode()
                node1.id = c_id
                node1.text = i['n']
                c_id += 1
                if 'conf' == i['i'][0:4]:
                    node1.type = 'conf'
                else:
                    node1.type = 'jour'
                node.nodes.append(node1.to_dict(corpus_id[node1.id]))
            field_tree.append(node.to_dict(corpus_id[node.id]))
        node0.nodes = field_tree
        display_tree.append(node0.to_dict(corpus_id[node0.id]))
    return display_tree


def tree(corpus_id):
    tree = get_dept_tree(corpus_id)
    return tree


class TreeNode():
    def __init__(self):
        self.id = 0
        self.text = "Node 1"
        self.state = {
            'checked': False,
        }
        self.nodes = []
        self.level = 2
        self.type = ''

    def to_dict(self, checked, expand=False):
        temp = {
            'id': self.id,
            'text': self.text,
            'state': {'checked': checked, 'expand': expand},
            'level': self.level,
            'type': self.type
        }
        if not len(self.nodes) == 0:
            temp['nodes'] = self.nodes
        return temp
