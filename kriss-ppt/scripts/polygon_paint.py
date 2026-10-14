"""Native geometry for resolved CSS polygons, border wedges and affine SVG strokes.

All vertices are derived from final browser geometry/styles. CSS clip-path clips
an existing border/shadow: it is NOT an instruction to outline the polygon.
"""
from __future__ import annotations
import math
import re
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from curved_paint import PathWriter, new_path_shape
from design_paint import UnsupportedPaint, split_css


def parse_polygon(value: str, width: float, height: float) -> list[tuple[float, float]]:
    m = re.fullmatch(r'polygon\((.*)\)', value.strip(), re.S)
    if not m: raise UnsupportedPaint('Only resolved simple CSS polygon clip paths are supported')
    terms = split_css(m[1])
    if terms and terms[0] in ('nonzero', 'evenodd'): terms = terms[1:]
    points = []
    for term in terms:
        xy = term.split()
        if len(xy) != 2: raise UnsupportedPaint('Unresolved polygon coordinate: ' + term)
        point = []
        for token, extent in zip(xy, (width, height)):
            match = re.fullmatch(r'([-+]?(?:\d*\.)?\d+)(px|%)?', token)
            if not match or (not match[2] and float(match[1]) != 0):
                raise UnsupportedPaint('Unresolved polygon unit: ' + token)
            point.append(float(match[1]) * (extent/100 if match[2] == '%' else 1))
        points.append(tuple(point))
    if len(points) < 3: raise UnsupportedPaint('Polygon needs at least three vertices')
    if any(not math.isfinite(v) for p in points for v in p): raise UnsupportedPaint('Non-finite polygon')
    if abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))) < 1e-7:
        raise UnsupportedPaint('Empty polygon')
    # Self-crossing clipping requires a general winding-rule Boolean engine.
    def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for i,(a,b) in enumerate(zip(points,points[1:]+points[:1])):
        for j,(c,d) in enumerate(zip(points,points[1:]+points[:1])):
            if j<=i+1 or (i==0 and j==len(points)-1): continue
            if cross(a,b,c)*cross(a,b,d)<-1e-9 and cross(c,d,a)*cross(c,d,b)<-1e-9:
                raise UnsupportedPaint('Self-intersecting polygon requires winding-rule support')
    return points


def set_polygon_path(shape, points, width, height, sx, sy, stroke=False):
    sp = shape._element.spPr
    for node in list(sp):
        if node.tag in (qn('a:prstGeom'), qn('a:custGeom')): sp.remove(node)
    geom = OxmlElement('a:custGeom')
    for tag in ('avLst','gdLst','ahLst','cxnLst'): geom.append(OxmlElement('a:'+tag))
    box = OxmlElement('a:rect')
    for k,v in [('l','0'),('t','0'),('r','w'),('b','h')]: box.set(k,v)
    geom.append(box)
    paths=OxmlElement('a:pathLst'); path=OxmlElement('a:path')
    path.set('w', str(max(1,round(width*sx*914400)))); path.set('h',str(max(1,round(height*sy*914400))))
    path.set('fill','norm'); path.set('stroke','1' if stroke else '0')
    paths.append(path); geom.append(paths); sp.insert(1,geom)
    pen=PathWriter(path,sx,sy); pen.move(points[0])
    for point in points[1:]: pen.line(point)
    pen.close()


def border_wedge(item, rgba):
    """Resolve zero-inner-size CSS border triangles as the clipped border face."""
    r=item['rect']; w,h=r['w'],r['h']
    widths={s:float(item.get('border'+s,{}).get('width',0)) for s in ('Top','Right','Bottom','Left')}
    if abs(w-widths['Left']-widths['Right'])>.12 or abs(h-widths['Top']-widths['Bottom'])>.12:
        return None
    painted=[s for s in widths if widths[s]>0 and rgba(item['border'+s]['color'])[3]>.001 and item['border'+s]['style']=='solid']
    if len(painted)!=1 or rgba(item.get('backgroundColor'))[3]>.001: return None
    side=painted[0]; center=(widths['Left'],widths['Top'])
    faces={'Top':[(0,0),(w,0),center],'Right':[(w,0),(w,h),center],
           'Bottom':[(w,h),(0,h),center],'Left':[(0,h),(0,0),center]}
    return {'points':faces[side],'color':item['border'+side]['color'],'source':'resolved CSS border wedge'}


def clip_to_rect(polygon, left, top, right, bottom):
    """Sutherland-Hodgman against an axis-aligned rectangular strip."""
    out=list(polygon)
    for axis,edge,sign in [(0,left,1),(0,right,-1),(1,top,1),(1,bottom,-1)]:
        inp=out;out=[]
        if not inp: break
        for a,b in zip(inp,inp[1:]+inp[:1]):
            ina=sign*(a[axis]-edge)>=-1e-9; inb=sign*(b[axis]-edge)>=-1e-9
            if ina:out.append(a)
            if ina!=inb:
                t=(edge-a[axis])/(b[axis]-a[axis]);out.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(2)))
    return out


def parse_flat_shadow(value):
    """Only zero-offset, zero-blur spread rings; do not approximate blurred inset."""
    m=re.fullmatch(r'(?:inset\s+)?(rgba?\([^)]*\)|#[a-fA-F\d]{3,8})\s+0px\s+0px\s+0px\s+([\d.]+)px(?:\s+inset)?',value.strip())
    if not m: return None
    return {'color':m[1],'spread':float(m[2]),'inset':'inset' in value}


def clipped_inset_bands(slide,item,sx,sy):
    shadow=item.get('flatShadow');points=item.get('clipPolygon')
    if not shadow or not shadow['inset'] or not points:return []
    r=item['rect'];w,h=r['w'],r['h'];v=shadow['spread'];out=[]
    for i,box in enumerate([(0,0,w,min(v,h)),(0,max(0,h-v),w,h),(0,v,min(v,w),h-v),(max(0,w-v),v,w,h-v)]):
        poly=clip_to_rect(points,*box)
        if len(poly)<3:continue
        sh,pen=new_path_shape(slide,r,sx,sy,shadow['color'],item.get('opacity',1),'kriss:shadow:'+item['id']+':'+str(i))
        pen.move(poly[0])
        for p in poly[1:]:pen.line(p)
        pen.close();out.append(sh)
    return out

