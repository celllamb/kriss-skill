"""Resolve native paint support and retain explicit unsupported-feature blockers."""
from design_paint import border_plan, parse_linear_gradient, UnsupportedPaint
from visual_primitives import rgba


def prepare_paint(text: dict, visual: dict) -> list[dict]:
    supported_gradients=set()
    supported_polygons=set()
    from polygon_paint import parse_polygon,border_wedge,parse_flat_shadow
    issues=[]
    for element in visual['elements']:
        if 'slide' in element.get('classes',[]):
            continue # Existing template background capture is unchanged.
        value=element.get('backgroundImage','none')
        clip=element.get('clipPath','none')
        if clip and clip!='none':
            try:
                element['clipPolygon']=parse_polygon(clip,element['rect']['w'],element['rect']['h'])
                supported_polygons.add(element['id'])
                if any(float(element.get('border'+side,{}).get('width',0))>0 for side in ['Top','Right','Bottom','Left']):
                    issues.append({'code':'unsupported-clipped-border','id':element['id'],'detail':'Clipping CSS box borders needs Boolean geometry; do not outline polygon'})
                if element.get('backgroundUrl'):
                    issues.append({'code':'unsupported-clipped-image','id':element['id']})
            except UnsupportedPaint as error:issues.append({'code':'unsupported-native-clip','id':element['id'],'detail':str(error)})
        wedge=border_wedge(element,rgba)
        if wedge:element['borderWedge']=wedge
        shadow=parse_flat_shadow(element.get('boxShadow','none'))
        if shadow:
            if shadow['inset'] and element.get('clipPolygon'):
                element['flatShadow']=shadow
            else:
                issues.append({'code':'unsupported-flat-spread-shadow','id':element['id'],'detail':element.get('boxShadow')})
        if value and value!='none' and not element.get('backgroundUrl'):
            try:
                if value.startswith('conic-gradient('):
                    from curved_paint import parse_step_conic
                    element['conic']=parse_step_conic(value,element,rgba)
                else:
                    element['gradient']=parse_linear_gradient(value,element['rect']['w'],element['rect']['h'])
                    element['gradient']['underlay']=element.get('backgroundColor','transparent')
                supported_gradients.add(element['id'])
            except UnsupportedPaint as error:
                issues.append({'code':'unsupported-native-gradient','id':element['id'],'detail':str(error)})
                element['unsupportedPaint']=True
        plan=border_plan(element,rgba)
        element['borderMode']=plan['mode']
        for side,b in plan['edges'].items():
            if b.get('style') not in ('solid','dashed','dotted'):
                issues.append({'code':'unsupported-border-style','id':element['id'],'side':side,'detail':b.get('style')})
        if plan['mode']=='edges' and float(element.get('borderRadiusPx') or 0)>0 and any(b.get('style')!='solid' for b in plan['edges'].values()):
            issues.append({'code':'unsupported-mixed-rounded-border','id':element['id'],'detail':'Mixed curved borders currently require solid sides.'})
    for block in text['blocks']:
        if block['id'] in supported_gradients and not any(e['id']==block['id'] and e.get('conic') for e in visual['elements']):
            block['mergeVisual']=True
    text['warnings']=[w for w in text['warnings'] if not((w['code']=='unsupported-component-background' and w['id'] in supported_gradients) or (w['code']=='unsupported-css-clip-path' and w['id'] in supported_polygons))]
    text['warnings'].extend(issues)
    return issues
