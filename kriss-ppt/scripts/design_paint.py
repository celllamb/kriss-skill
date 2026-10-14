"""CSS paint translators used by the native exporter.

This module never changes DOM layout. It translates the captured CSS value and
border box. Unsupported CSS is an explicit error, not a substitute solid fill.
"""
from __future__ import annotations
import math
import re
from typing import Callable
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn

class UnsupportedPaint(ValueError):
    pass


def split_css(value: str) -> list[str]:
    """Split commas at the outermost CSS function level."""
    result, start, depth = [], 0, 0
    for i, char in enumerate(value):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            result.append(value[start:i].strip())
            start = i + 1
    if depth != 0:
        raise UnsupportedPaint('Unbalanced CSS function')
    result.append(value[start:].strip())
    return result


def parse_linear_gradient(value: str, width: float, height: float) -> dict | None:
    """Resolve CSS linear/repeating-linear gradients into native gradient stops.

    Supports sRGB hex/rgb(a) stops, CSS angles/to-corner directions, percentages,
    px, omitted positions and two-position color stops. Color hints, color-space
    modifiers, conic/radial and layered backgrounds remain blockers.
    """
    if not value or value == 'none':
        return None
    m = re.fullmatch(r'(repeating-)?linear-gradient\((.*)\)', value.strip(), re.S)
    if not m:
        raise UnsupportedPaint('Only a single linear/repeating-linear gradient is supported')
    terms = split_css(m[2])
    angle = 180.0
    direction = terms[0].lower()
    a = re.fullmatch(r'([-+\d.]+)(deg|grad|rad|turn)', direction)
    if a:
        angle = float(a[1]) * {'deg': 1, 'grad': .9, 'rad': 180/math.pi, 'turn': 360}[a[2]]
        terms.pop(0)
    elif direction.startswith('to '):
        sides = direction.split()[1:]
        if not sides or any(x not in ('left','right','top','bottom') for x in sides) or len(sides)>2:
            raise UnsupportedPaint('Invalid gradient direction')
        dx = (1 if 'right' in sides else -1 if 'left' in sides else 0)
        dy = (1 if 'bottom' in sides else -1 if 'top' in sides else 0)
        if dx and dy:
            # CSS "magic corners": gradient normal perpendicular to other diagonal.
            dx, dy = dx*height, dy*width
        angle = math.degrees(math.atan2(dx, -dy))
        terms.pop(0)
    dx, dy = math.sin(math.radians(angle)), -math.cos(math.radians(angle))
    length = abs(width*dx) + abs(height*dy)
    if length <= 0:
        raise UnsupportedPaint('Empty gradient box')
    raw = []
    for term in terms:
        cm = re.match(r'^(rgba?\([^)]*\)|#[0-9a-fA-F]{3,8}|transparent|white|black)\s*(.*)$', term, re.I)
        if not cm:
            raise UnsupportedPaint('Unsupported color stop: '+term)
        color = {'white':'#ffffff','black':'#000000'}.get(cm[1].lower(),cm[1])
        pos = cm[2].split()
        if len(pos)>2:
            raise UnsupportedPaint('Gradient hints/complex stop positions are unsupported')
        if not pos:
            raw.append([color,None])
        for token in pos:
            pm=re.fullmatch(r'([-+\d.]+)(%|px)?', token)
            if not pm or (not pm[2] and float(pm[1])!=0):
                raise UnsupportedPaint('Unsupported stop unit: '+token)
            raw.append([color,float(pm[1])/100 if pm[2]=='%' else float(pm[1])/length])
    if len(raw)<2:
        raise UnsupportedPaint('At least two color stops are required')
    if raw[0][1] is None:raw[0][1]=0.0
    if raw[-1][1] is None:raw[-1][1]=1.0
    # CSS fix-up clamps explicitly decreasing positions; then distributes omissions.
    previous=raw[0][1]
    for stop in raw[1:]:
        if stop[1] is not None:
            stop[1]=max(previous,stop[1]);previous=stop[1]
    begin=0
    while begin<len(raw)-1:
        end=begin+1
        while raw[end][1] is None:end+=1
        for k in range(begin+1,end):
            raw[k][1]=raw[begin][1]+(raw[end][1]-raw[begin][1])*(k-begin)/(end-begin)
        begin=end
    if m[1]:
        period=raw[-1][1]-raw[0][1]
        if period<=0:
            return {'angle':(angle-90)%360,'stops':[[0,raw[-1][0]],[1,raw[-1][0]]], 'css':value}
        first=math.floor((0-raw[-1][1])/period)
        last=math.ceil((1-raw[0][1])/period)
        if (last-first+1)*len(raw)>2048:
            raise UnsupportedPaint('Repeating gradient exceeds 2048 native stops')
        raw=[[c,p+i*period] for i in range(first,last+1) for c,p in raw]
    return {'angle':(angle-90)%360,'stops':[[p,c] for c,p in raw], 'css':value}


def _interpolate(ca,cb,t):
    """Premultiplied sRGB interpolation, matching CSS transparent-stop behavior."""
    alpha=ca[3]+(cb[3]-ca[3])*t
    rgb=[(ca[i]*ca[3]*(1-t)+cb[i]*cb[3]*t)/alpha if alpha else 0 for i in range(3)]
    return tuple(round(v) for v in rgb)+(alpha,)


def normalized_stops(spec:dict, rgba:Callable) -> list:
    raw=[(p,rgba(c) if isinstance(c,str) else tuple(c)) for p,c in spec['stops']]
    def at(p, right=False):
        equal=[c for x,c in raw if abs(x-p)<1e-10]
        if equal:return equal[-1] if right else equal[0]
        if p<raw[0][0]:return raw[0][1]
        for (x,a),(y,b) in zip(raw,raw[1:]):
            if x<p<y:return _interpolate(a,b,(p-x)/(y-x))
        return raw[-1][1]
    inside=[(p,c) for p,c in raw if 0<=p<=1]
    if not inside or inside[0][0]>0:inside.insert(0,(0,at(0,True)))
    if inside[-1][0]<1:inside.append((1,at(1)))
    # Coincident stops are legal in OOXML but some native renderers reorder them.
    # Use its smallest position quantum (1 / 100000 of the gradient line) to keep
    # the order stable. This is <= 0.013 px at 1280px, not a widened QA tolerance.
    grouped=[]
    for p,c in inside:
        position=round(p*100000)
        if grouped and grouped[-1][0]==position:grouped[-1][1].append(c)
        else:grouped.append([position,[c]])
    stable=[]
    for pos,colors in grouped:
        if pos==0:stable.append((0,colors[-1]))
        elif pos==100000:stable.append((1,colors[0]))
        elif colors[0]!=colors[-1]:
            if stable and round(stable[-1][0]*100000)>=pos-1:
                raise UnsupportedPaint('Hard stops exceed native gradient coordinate precision')
            stable.extend([((pos-1)/100000,colors[0]),(pos/100000,colors[-1])])
        else:stable.append((pos/100000,colors[-1]))
    return stable


def set_gradient(shape,spec:dict,rgba:Callable,opacity:float=1.0):
    """Native DrawingML gradient, no screenshot and no simulated small strips."""
    sp=shape._element.spPr
    for node in list(sp):
        if node.tag in {qn('a:'+s) for s in ('solidFill','noFill','gradFill','pattFill','blipFill','grpFill')}:
            sp.remove(node)
    grad=OxmlElement('a:gradFill');grad.set('rotWithShape','1')
    stops=OxmlElement('a:gsLst')
    for p,(r,g,b,a) in normalized_stops(spec,rgba):
        if spec.get('underlay'):
            br,bg,bb,ba=rgba(spec['underlay']);oa=a+ba*(1-a)
            r,g,b=[round((v*a+bv*ba*(1-a))/oa) if oa else 0 for v,bv in zip((r,g,b),(br,bg,bb))];a=oa
        gs=OxmlElement('a:gs');gs.set('pos',str(round(p*100000)))
        col=OxmlElement('a:srgbClr');col.set('val',f'{r:02X}{g:02X}{b:02X}')
        alpha=max(0,min(1,a*opacity))
        if alpha<.99999:
            al=OxmlElement('a:alpha');al.set('val',str(round(alpha*100000)));col.append(al)
        gs.append(col);stops.append(gs)
    grad.append(stops)
    lin=OxmlElement('a:lin');lin.set('ang',str(round(spec['angle']*60000)%21600000));lin.set('scaled','0');grad.append(lin)
    # OOXML order: xfrm, geometry, fill, line, effects.
    idx=next((i for i,n in enumerate(sp) if n.tag in (qn('a:ln'),qn('a:effectLst'),qn('a:effectDag'),qn('a:scene3d'),qn('a:sp3d'))),len(sp))
    sp.insert(idx,grad)


def border_plan(item:dict,rgba:Callable) -> dict:
    edges={side:item.get('border'+side.title(),{}) for side in ('top','right','bottom','left')}
    def visible(b):return float(b.get('width') or 0)>0 and b.get('style') not in ('none','hidden') and rgba(b.get('color'))[3]>.001
    active={side:b for side,b in edges.items() if visible(b)}
    def key(b):return (float(b.get('width',0)),b.get('color'),b.get('style'))
    if len(active)==4 and len({key(b) for b in active.values()})==1:
        return {'mode':'uniform','edges':active,'outline':next(iter(active.values()))}
    rounded=any(float(re.match(r'[\d.]+',str(v)).group())>0 for v in (item.get('borderRadii') or [item.get('borderRadius','0')]) if re.match(r'[\d.]+',str(v)))
    if len(active)==1 and not rounded and next(iter(active.values())).get('style')=='solid' and item.get('backgroundImage','none')=='none':
        side,b=next(iter(active.items()));axis=item['rect']['w'] if side in ('left','right') else item['rect']['h']
        fraction=min(1,float(b['width'])/max(axis,1e-9));bg=item.get('backgroundColor','transparent');color=b['color']
        if side in ('left','top'):stops=[[0,color],[fraction,color],[fraction,bg],[1,bg]]
        else:stops=[[0,bg],[1-fraction,bg],[1-fraction,color],[1,color]]
        return {'mode':'single-side-fill','edges':active,'gradient':{'angle':0 if side in ('left','right') else 90,'stops':stops}}
    return {'mode':'edges' if active else 'none','edges':active}
