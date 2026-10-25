"""Inspect official KRISS PPTX master typography; never silently replace a font."""
from __future__ import annotations
import json
from pathlib import Path
from pptx import Presentation
from pptx.oxml.ns import qn
from master_template import TEMPLATE


def specification(path:Path=TEMPLATE)->dict:
    prs=Presentation(path)
    root=prs.slide_masters[0]._element
    styles=root.xpath('.//p:txStyles')
    if len(styles)!=1:raise ValueError('KRISS template missing master text styles')
    out={'font':None,'title_pt':None,'body_levels_pt':[], 'cover_title_pt':None}
    title=styles[0].find(qn('p:titleStyle'))
    body=styles[0].find(qn('p:bodyStyle'))
    title_pr=title.find(qn('a:lvl1pPr')).find(qn('a:defRPr'))
    out['title_pt']=int(title_pr.get('sz'))/100
    for tag in ('latin','ea'):
        node=title_pr.find(qn('a:'+tag))
        if node is not None and node.get('typeface') and not node.get('typeface').startswith('+'):
            out['font']=node.get('typeface');break
    for ix in range(1,6):
        pr=body.find(qn('a:lvl'+str(ix)+'pPr'))
        if pr is None:break
        rPr=pr.find(qn('a:defRPr'))
        if rPr is None:break
        out['body_levels_pt'].append(int(rPr.get('sz'))/100)
    cover=prs.slide_layouts[0]
    for sh in cover.shapes:
        if getattr(sh,'is_placeholder',False) and int(sh.placeholder_format.type) in (1,3):
            sizes=[int(x.get('sz'))/100 for x in sh._element.findall('.//'+qn('a:defRPr')) if x.get('sz')]
            if sizes:out['cover_title_pt']=sizes[0]
            break
    if not(out['font'] and out['title_pt'] and out['cover_title_pt']):
        raise ValueError('Incomplete native typography rules')
    return out


def check_expected(spec:dict):
    if spec['font']!='나눔바른고딕' or spec['title_pt']!=28 or spec['cover_title_pt']!=40 or spec['body_levels_pt']!=[28,24,20,18,18]:
        raise ValueError('Supplied KRISS original font or master sizes changed: '+json.dumps(spec,ensure_ascii=False))


if __name__=='__main__':
    rules=specification();check_expected(rules)
    print(json.dumps(rules,ensure_ascii=False,indent=2))
