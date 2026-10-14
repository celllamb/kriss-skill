"""Editable native paths for CSS mixed rounded borders and flat conic sectors.

Paths are derived from captured border boxes/radii/widths. No pattern IDs, subject
coordinates, screenshots, text offsets or per-slide calibration are used.
"""
from __future__ import annotations
import math
import re
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches
from design_paint import split_css, UnsupportedPaint


def _pt(parent, x, y, sx, sy):
    point=OxmlElement('a:pt');point.set('x',str(round(x*sx*914400)));point.set('y',str(round(y*sy*914400)));parent.append(point)


class PathWriter:
    def __init__(self, path, sx, sy):self.path,self.sx,self.sy=path,sx,sy
    def move(self, point):
        node=OxmlElement('a:moveTo');_pt(node,*point,self.sx,self.sy);self.path.append(node)
    def line(self, point):
        node=OxmlElement('a:lnTo');_pt(node,*point,self.sx,self.sy);self.path.append(node)
    def arc(self, center, radii, start, end):
        rx,ry=radii;cx,cy=center
        if rx<=0 or ry<=0:
            self.line((cx+rx*math.cos(end),cy+ry*math.sin(end)));return
        # Cubic ellipse arcs split at <=30 degrees; maximum geometric error is
        # below 0.001 px for the slide-sized radii supported here.
        segments=max(1,math.ceil(abs(end-start)/(math.pi/6)))
        for i in range(segments):
            a=start+(end-start)*i/segments;b=start+(end-start)*(i+1)/segments
            k=4/3*math.tan((b-a)/4)
            p1=(cx+rx*(math.cos(a)-k*math.sin(a)),cy+ry*(math.sin(a)+k*math.cos(a)))
            p2=(cx+rx*(math.cos(b)+k*math.sin(b)),cy+ry*(math.sin(b)-k*math.cos(b)))
            p3=(cx+rx*math.cos(b),cy+ry*math.sin(b))
            node=OxmlElement('a:cubicBezTo')
            for point in (p1,p2,p3):_pt(node,*point,self.sx,self.sy)
            self.path.append(node)
    def close(self):self.path.append(OxmlElement('a:close'))


def new_path_shape(slide, rect, sx, sy, color, opacity, name):
    from visual_primitives import remove_theme_style,clear_shape_effects,set_shape_fill
    shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(rect['x']*sx),Inches(rect['y']*sy),Inches(rect['w']*sx),Inches(rect['h']*sy))
    remove_theme_style(shape);clear_shape_effects(shape);shape.line.fill.background();set_shape_fill(shape,color,opacity)
    sp=shape._element.spPr;sp.remove(sp.find(qn('a:prstGeom')))
    geom=OxmlElement('a:custGeom')
    for kind in ('avLst','gdLst','ahLst','cxnLst'):geom.append(OxmlElement('a:'+kind))
    box=OxmlElement('a:rect')
    for key,value in [('l','0'),('t','0'),('r','w'),('b','h')]:box.set(key,value)
    geom.append(box)
    paths=OxmlElement('a:pathLst');path=OxmlElement('a:path')
    path.set('w',str(max(1,round(rect['w']*sx*914400))));path.set('h',str(max(1,round(rect['h']*sy*914400))))
    path.set('stroke','0');path.set('fill','norm');paths.append(path);geom.append(paths)
    sp.insert(1,geom);shape.name=name
    return shape,PathWriter(path,sx,sy)


def _intersection(rx, ry, bx, by, inner=False):
    """CSS corner join ray from outer rectangular corner towards inner corner."""
    ix,iy=(bx,by) if inner else (0.,0.)
    a=max(0.,rx-bx) if inner else rx;b=max(0.,ry-by) if inner else ry
    center=(ix+a,iy+b)
    if a<=0 or b<=0:return (ix,iy),center,(a,b)
    dx,dy=bx,by
    if dx==dy==0:dx=dy=1.
    aa=(dx/a)**2+(dy/b)**2;bb=-2*(center[0]*dx/a**2+center[1]*dy/b**2)
    cc=(center[0]/a)**2+(center[1]/b)**2-1
    t=(-bb-math.sqrt(max(0.,bb*bb-4*aa*cc)))/(2*aa)
    return (dx*t,dy*t),center,(a,b)


def corner_radii(item: dict) -> list[tuple[float,float]]:
    """Resolve all four computed CSS corner pairs, including CSS overlap scaling."""
    w,h=item['rect']['w'],item['rect']['h']
    values=item.get('borderRadii') or [item.get('borderRadius','0px')]*4
    pairs=[]
    for value in values:
        tokens=str(value).split()
        if not tokens or len(tokens)>2:raise UnsupportedPaint('Unresolved CSS corner radius')
        if len(tokens)==1:tokens*=2
        def length(token,extent):
            if token.endswith('%'):return float(token[:-1])*extent/100
            if token.endswith('px'):return float(token[:-2])
            return float(token)
        pairs.append((max(0,length(tokens[0],w)),max(0,length(tokens[1],h))))
    denominators=[(w,pairs[0][0]+pairs[1][0]),(w,pairs[3][0]+pairs[2][0]),
                  (h,pairs[0][1]+pairs[3][1]),(h,pairs[1][1]+pairs[2][1])]
    factor=min([1.]+[extent/total for extent,total in denominators if total>0])
    return [(x*factor,y*factor) for x,y in pairs]


def requires_corner_path(item: dict) -> bool:
    pairs=corner_radii(item);w,h=item['rect']['w'],item['rect']['h']
    equal=all(abs(x-pairs[0][0])<1e-7 and abs(y-pairs[0][1])<1e-7 for x,y in pairs)
    circle_corners=equal and abs(pairs[0][0]-pairs[0][1])<1e-7
    ellipse=equal and abs(pairs[0][0]-w/2)<1e-7 and abs(pairs[0][1]-h/2)<1e-7
    return not(circle_corners or ellipse)


def set_corner_path(shape, item, sx, sy, border_inset=0.):
    """One editable native custom shape; no corner boxes or screenshot substitute."""
    w=item['rect']['w']-2*border_inset;h=item['rect']['h']-2*border_inset
    radii=[(max(0,x-border_inset),max(0,y-border_inset)) for x,y in corner_radii(item)]
    sp=shape._element.spPr
    for child in list(sp):
        if child.tag in (qn('a:prstGeom'),qn('a:custGeom')):sp.remove(child)
    geom=OxmlElement('a:custGeom')
    for name in ('avLst','gdLst','ahLst','cxnLst'):geom.append(OxmlElement('a:'+name))
    box=OxmlElement('a:rect')
    for key,value in [('l','0'),('t','0'),('r','w'),('b','h')]:box.set(key,value)
    geom.append(box);paths=OxmlElement('a:pathLst');path=OxmlElement('a:path')
    path.set('w',str(max(1,round(w*sx*914400))));path.set('h',str(max(1,round(h*sy*914400))))
    path.set('fill','norm');path.set('stroke','1');paths.append(path);geom.append(paths);sp.insert(1,geom)
    pen=PathWriter(path,sx,sy);tl,tr,br,bl=radii
    pen.move((tl[0],0));pen.line((w-tr[0],0));pen.arc((w-tr[0],tr[1]),tr,-math.pi/2,0)
    pen.line((w,h-br[1]));pen.arc((w-br[0],h-br[1]),br,0,math.pi/2)
    pen.line((bl[0],h));pen.arc((bl[0],h-bl[1]),bl,math.pi/2,math.pi)
    pen.line((0,tl[1]));pen.arc(tl,tl,math.pi,3*math.pi/2);pen.close()


def rounded_edges(slide,item,sx,sy,edges):
    rect=item['rect'];w,h=rect['w'],rect['h'];radii_by_corner=corner_radii(item)
    widths={side:float(item.get('border'+side.title(),{}).get('width') or 0) for side in ('top','right','bottom','left')}
    # Corner order clockwise: top-left, top-right, bottom-right, bottom-left.
    specifications=[(0,0,1,1,'left','top'),(w,0,-1,1,'right','top'),(w,h,-1,-1,'right','bottom'),(0,h,1,-1,'left','bottom')]
    corners=[]
    for (ox,oy,dx,dy,xside,yside),(rx,ry) in zip(specifications,radii_by_corner):
        pair=[]
        for inner in (False,True):
            point,center,radii=_intersection(rx,ry,widths[xside],widths[yside],inner)
            point=(ox+dx*point[0],oy+dy*point[1]);center=(ox+dx*center[0],oy+dy*center[1])
            angle=math.atan2((point[1]-center[1])/max(radii[1],1e-30),(point[0]-center[0])/max(radii[0],1e-30))%(2*math.pi)
            pair.append({'point':point,'center':center,'radii':radii,'angle':angle})
        corners.append(pair)
    out=[]
    for j,side in enumerate(('top','right','bottom','left')):
        if side not in edges:continue
        style=edges[side]
        if style['style']!='solid':raise UnsupportedPaint('Mixed rounded borders currently require solid sides')
        shape,path=new_path_shape(slide,rect,sx,sy,style['color'],float(item.get('opacity',1)),'kriss:edge:'+item['id']+':'+side)
        first,second=corners[j],corners[(j+1)%4]
        tangent=(3*math.pi/2+j*math.pi/2)%(2*math.pi)
        def after(value,minimum):
            while value<minimum-1e-12:value+=2*math.pi
            return value
        # Outer half-corner, straight edge, outer half-corner; then reverse inner boundary.
        a0=first[0]['angle'];t=after(tangent,a0);a1=after(second[0]['angle'],t)
        path.move(first[0]['point']);path.arc(first[0]['center'],first[0]['radii'],a0,t)
        cc=second[0];path.line((cc['center'][0]+cc['radii'][0]*math.cos(t),cc['center'][1]+cc['radii'][1]*math.sin(t)))
        path.arc(cc['center'],cc['radii'],t,a1);path.line(second[1]['point'])
        ia1=second[1]['angle'];it=tangent
        while it>ia1+1e-12:it-=2*math.pi
        ia0=first[1]['angle']
        while ia0>it+1e-12:ia0-=2*math.pi
        path.arc(second[1]['center'],second[1]['radii'],ia1,it)
        cc=first[1];path.line((cc['center'][0]+cc['radii'][0]*math.cos(it),cc['center'][1]+cc['radii'][1]*math.sin(it)))
        path.arc(cc['center'],cc['radii'],it,ia0);path.close();out.append(shape)
    return out


def parse_step_conic(value: str, item: dict, rgba) -> dict:
    match=re.fullmatch(r'conic-gradient\((.*)\)',value.strip(),re.S)
    if not match:raise UnsupportedPaint('Only centered flat-color conic sectors are supported')
    rect=item['rect']
    if abs(rect['w']-rect['h'])>.1 or not str(item.get('borderRadius','')).startswith('50%'):
        raise UnsupportedPaint('Conic sectors require the authored circular clipping geometry')
    raw=[]
    for term in split_css(match[1]):
        stop=re.fullmatch(r'(rgba?\([^)]*\)|#[0-9a-fA-F]{3,8}|transparent)\s*(.*)',term)
        if not stop:raise UnsupportedPaint('Conic from/at modifiers and color syntax are not supported')
        positions=stop[2].split()
        if not positions:raw.append([stop[1],None])
        for token in positions:
            pm=re.fullmatch(r'([-+\d.]+)(deg|grad|rad|turn|%)?',token)
            if not pm:raise UnsupportedPaint('Unsupported conic position')
            unit=pm[2] or 'deg';factor={'deg':1/360,'grad':1/400,'rad':1/(2*math.pi),'turn':1,'%':.01}[unit]
            raw.append([stop[1],float(pm[1])*factor])
    if len(raw)<2:raise UnsupportedPaint('Conic sectors need two or more stops')
    if raw[0][1] is None:raw[0][1]=0.
    if raw[-1][1] is None:raw[-1][1]=1.
    if any(p is None for c,p in raw):raise UnsupportedPaint('Specify all conic sector boundaries explicitly')
    previous=raw[0][1]
    for stop in raw:stop[1]=max(previous,stop[1]);previous=stop[1]
    if raw[0][1]>0:raw.insert(0,[raw[0][0],0.])
    if raw[-1][1]<1:raw.append([raw[-1][0],1.])
    sectors=[]
    for (ca,a),(cb,b) in zip(raw,raw[1:]):
        a=max(0.,a);b=min(1.,b)
        if b<=a:continue
        if rgba(ca)!=rgba(cb):raise UnsupportedPaint('Continuous conic color interpolation is not supported')
        sectors.append({'start':a,'end':b,'color':ca})
    return {'sectors':sectors,'css':value}


def conic_sectors(slide,item,sx,sy):
    rect=item['rect'];radius=rect['w']/2;center=(radius,radius);result=[]
    for i,sector in enumerate(item['conic']['sectors']):
        shape,path=new_path_shape(slide,rect,sx,sy,sector['color'],item.get('opacity',1),'kriss:sector:'+item['id']+':'+str(i))
        a=sector['start']*2*math.pi-math.pi/2;b=sector['end']*2*math.pi-math.pi/2
        path.move(center);path.line((center[0]+radius*math.cos(a),center[1]+radius*math.sin(a)))
        path.arc(center,(radius,radius),a,b);path.close();result.append(shape)
    return result
