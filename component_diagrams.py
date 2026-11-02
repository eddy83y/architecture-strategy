"""Render compact UML component overviews from content/components.json.

A dependency points from its consumer to its provider. Storage replication is
an explicitly different relationship. Layout uses the existing project skin;
SVGs scale to fit rather than scroll, as requested for this project.
"""
from pathlib import Path
from html import escape
import heapq
import itertools
import json

PAPER, INK, MUTED, SOFT, RULE, ACCENT, LINK = '#f5f5f5', '#2d3142', '#4f5d75', '#5a6580', '#bfc0c0', '#bf4520', '#2e5aa8'
SANS = "'Geist', 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"
FONT_URL = 'https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Geist:wght@400;500;600&family=Noto+Sans+KR:wght@400;500;600&display=swap'
STEP = 8
DIRECTIONS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
SIDE_DIR = {'right': 0, 'bottom': 1, 'left': 2, 'top': 3}
OPPOSITE = {'right': 'left', 'left': 'right', 'top': 'bottom', 'bottom': 'top'}


def text(x, y, value, size=16, color=INK, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" font-family="{escape(SANS, quote=True)}" text-anchor="{anchor}">{escape(value)}</text>'


def side_for(a, b):
    dx, dy = b['x']-a['x'], b['y']-a['y']
    if abs(dx) >= abs(dy) and dx:
        return 'right' if dx > 0 else 'left'
    return 'bottom' if dy > 0 else 'top'


def port(n, side, index, count):
    length = n['height'] if side in ('left', 'right') else n['width']
    offset = round(length*(index+1)/(count+1)/STEP)*STEP
    if side == 'left': return (n['x'], n['y']+offset)
    if side == 'right': return (n['x']+n['width'], n['y']+offset)
    if side == 'top': return (n['x']+offset, n['y'])
    return (n['x']+offset, n['y']+n['height'])


def segment_points(a, b):
    dx = (b[0] > a[0])-(b[0] < a[0]); dy = (b[1] > a[1])-(b[1] < a[1])
    assert not (dx and dy)
    n = int((abs(b[0]-a[0])+abs(b[1]-a[1]))/STEP)
    return [(a[0]+i*STEP*dx, a[1]+i*STEP*dy) for i in range(n+1)]


def simplify(points):
    result=[]
    for p in points:
        if result and p == result[-1]:continue
        if len(result)>1 and ((result[-2][0]==result[-1][0]==p[0]) or (result[-2][1]==result[-1][1]==p[1])):
            result[-1]=p
        else:result.append(p)
    return result


def route_all(nodes, edges):
    by_id={n['id']:n for n in nodes}; slots={}; prepared=[]
    for i,e in enumerate(edges):
        a,b=by_id[e['source']],by_id[e['target']]
        sa=e.get('source_side',side_for(a,b)); sb=e.get('target_side',OPPOSITE[sa])
        prepared.append((i,sa,sb))
        slots.setdefault((a['id'],sa),[]).append((i,'source'))
        slots.setdefault((b['id'],sb),[]).append((i,'target'))
    ports={}
    for (nid,side),items in slots.items():
        for j,key in enumerate(items):ports[key]=port(by_id[nid],side,j,len(items))
    blocked=set()
    for n in nodes:
        for x in range(n['x']-16,n['x']+n['width']+17,STEP):
            for y in range(n['y']-16,n['y']+n['height']+17,STEP):blocked.add((x,y))
    occupied={}  # Grid vertices mapped to the orientations of earlier wires.
    paths={}
    # Reserve detours for long relationships before routing short local links.
    prepared.sort(key=lambda item:sum(abs(a-b) for a,b in zip(ports[(item[0],'source')],ports[(item[0],'target')])) , reverse=True)
    for i,sa,sb in prepared:
        source,target=ports[(i,'source')],ports[(i,'target')]
        da=DIRECTIONS[SIDE_DIR[sa]]; db=DIRECTIONS[SIDE_DIR[sb]]
        start=(source[0]+24*da[0],source[1]+24*da[1]); goal=(target[0]+24*db[0],target[1]+24*db[1])
        points=None
        for allow_crossing in (False,True):
            counter=itertools.count(); initial=(start[0],start[1],SIDE_DIR[sa]); cost={initial:0}; previous={}
            queue=[(0,next(counter),initial)]
            final=None
            while queue:
                _,_,state=heapq.heappop(queue);x,y,last=state;cur=cost[state]
                if (x,y)==goal:
                    final=state;break
                for direction,(dx,dy) in enumerate(DIRECTIONS):
                    if direction==(last+2)%4:continue
                    nx,ny=x+dx*STEP,y+dy*STEP
                    if not (24<=nx<=1256 and 104<=ny<=648):continue
                    if (nx,ny) in blocked:continue
                    orientation=direction%2; extra=0;invalid=False
                    for ox in range(nx-8,nx+9,STEP):
                        for oy in range(ny-8,ny+9,STEP):
                            used=occupied.get((ox,oy),set())
                            if not used:continue
                            if allow_crossing and (1-orientation) in used and orientation not in used:
                                extra+=100
                            else:invalid=True
                    if invalid:continue
                    next_state=(nx,ny,direction);value=cur+1+(6 if direction!=last else 0)+extra
                    if value<cost.get(next_state,float('inf')):
                        cost[next_state]=value;previous[next_state]=state
                        h=(abs(nx-goal[0])+abs(ny-goal[1]))/STEP
                        heapq.heappush(queue,(value+h,next(counter),next_state))
            if final:
                trail=[]
                while True:
                    trail.append((final[0],final[1]))
                    if final==initial:break
                    final=previous[final]
                points=simplify([source]+list(reversed(trail))+[target]);break
        if points is None:raise ValueError(f"No safe route for {edges[i]}")
        paths[i]=points
        for a,b in zip(points,points[1:]):
            orientation=0 if a[1]==b[1] else 1
            for p in segment_points(a,b):occupied.setdefault(p,set()).add(orientation)
    return [paths[i] for i in range(len(edges))]


def crossing_points(path, older_paths):
    found=[]
    for a,b in zip(path,path[1:]):
        for old in older_paths:
            for c,d in zip(old,old[1:]):
                if a[1]==b[1] and c[0]==d[0] and min(a[0],b[0])+12<c[0]<max(a[0],b[0])-12 and min(c[1],d[1])+12<a[1]<max(c[1],d[1])-12:
                    found.append((c[0],a[1]))
                if a[0]==b[0] and c[1]==d[1] and min(a[1],b[1])+12<c[1]<max(a[1],b[1])-12 and min(c[0],d[0])+12<a[0]<max(c[0],d[0])-12:
                    found.append((a[0],c[1]))
    return set(found)


def svg_path(points, crossings=()):
    parts=[f'M {points[0][0]} {points[0][1]}']
    for i in range(1,len(points)):
        start=points[i-1];end=points[i]
        dx=(end[0]>start[0])-(end[0]<start[0]);dy=(end[1]>start[1])-(end[1]<start[1])
        corner=i<len(points)-1
        stop=(end[0]-8*dx,end[1]-8*dy) if corner else end
        hops=[p for p in crossings if (dx and p[1]==start[1] and min(start[0],stop[0])+8<p[0]<max(start[0],stop[0])-8) or (dy and p[0]==start[0] and min(start[1],stop[1])+8<p[1]<max(start[1],stop[1])-8)]
        hops.sort(key=lambda p:abs(p[0]-start[0])+abs(p[1]-start[1]))
        for x,y in hops:
            parts.append(f'L {x-8*dx} {y-8*dy}')
            # A rounded bridge is distinguished from the normal 8px elbows.
            parts.append(f'Q {x-8*dx+8*dy} {y-8*dy-8*dx} {x+8*dy} {y-8*dx}')
            parts.append(f'Q {x+8*dx+8*dy} {y+8*dy-8*dx} {x+8*dx} {y+8*dy}')
        parts.append(f'L {stop[0]} {stop[1]}')
        if corner:
            nxt=points[i+1];dx2=(nxt[0]>end[0])-(nxt[0]<end[0]);dy2=(nxt[1]>end[1])-(nxt[1]<end[1])
            parts.append(f'Q {end[0]} {end[1]} {end[0]+8*dx2} {end[1]+8*dy2}')
    return ' '.join(parts)


def arrowhead(tip, previous, color):
    dx=(tip[0]>previous[0])-(tip[0]<previous[0]);dy=(tip[1]>previous[1])-(tip[1]<previous[1])
    x,y=tip
    return f'<path data-role="arrowhead" d="M {x-10*dx+5*dy} {y-10*dy-5*dx} L {x} {y} L {x-10*dx-5*dy} {y-10*dy+5*dx}" fill="none" stroke="{color}" stroke-width="1.5"/>'


def node_svg(n):
    x,y,w,h=n['x'],n['y'],n['width'],n['height'];kind=n['kind'];focus=n.get('focus',False)
    stroke=ACCENT if focus else (LINK if kind=='external' else INK)
    fill='rgba(191,69,32,.08)' if focus else ('#ececec' if kind=='store' else PAPER)
    tag={'store':'«datastore»','external':'«external system»','instance':'«component instance»'}.get(kind,'«component»')
    dash=' stroke-dasharray="6,4"' if kind=='external' else ''
    out=f'<g data-node-id="{n["id"]}" data-kind="{kind}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/><rect data-role="bounds" x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>'
    out+=text(x+16,y+22,tag,12,SOFT)
    out+=text(x+16,y+52,n['title'],20,INK,600)
    out+=text(x+16,y+78,n['subtitle'],14,MUTED)
    if kind in ('component','instance'):
        ix,iy=x+w-36,y+12
        out+=f'<rect x="{ix}" y="{iy}" width="20" height="24" fill="{PAPER}" stroke="{stroke}"/><rect x="{ix-4}" y="{iy+4}" width="8" height="5" fill="{PAPER}" stroke="{stroke}"/><rect x="{ix-4}" y="{iy+15}" width="8" height="5" fill="{PAPER}" stroke="{stroke}"/>'
    return out+'</g>'


def validate(spec,paths):
    nodes=spec['nodes'];edges=spec['edges'];ids={n['id'] for n in nodes}
    assert len(nodes)<=9 and len(edges)<=12 and len(ids)==len(nodes)
    assert sum(n.get('focus',False) for n in nodes)<=2
    for n in nodes:
        assert all(n[k]%4==0 for k in ('x','y','width','height'))
        for other in nodes:
            if n is other:continue
            assert n['x']+n['width']<=other['x'] or other['x']+other['width']<=n['x'] or n['y']+n['height']<=other['y'] or other['y']+other['height']<=n['y']
    attaches=set()
    for e,path in zip(edges,paths):
        assert e['source'] in ids and e['target'] in ids
        for nid,p in [(e['source'],path[0]),(e['target'],path[-1])]:
            assert (nid,p) not in attaches,(nid,p);attaches.add((nid,p))
        for a,b in zip(path,path[1:]):
            assert a[0]==b[0] or a[1]==b[1]
            for px,py in segment_points(a,b)[1:-1]:
                for n in nodes:
                    assert not (n['x']<px<n['x']+n['width'] and n['y']<py<n['y']+n['height']),(e,n['id'],(px,py))


def render(sid,spec):
    slug=sid.lower()+'-component';paths=route_all(spec['nodes'],spec['edges']);validate(spec,paths)
    out=f'<svg class="component-diagram" style="display:block;width:100%;max-width:100%;min-width:0;height:auto" viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc"><title id="{slug}-title">{sid} 핵심 컴포넌트 구성</title><desc id="{slug}-desc">{escape(spec["description"])}</desc><defs>'
    for suffix,color in [('dependency',MUTED),('replication',ACCENT),('external',LINK)]:
        out+=f'<marker id="{slug}-{suffix}" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="{color}" stroke-width="1.2"/></marker>'
    out+='</defs>'+f'<rect width="1280" height="720" fill="{PAPER}"/>'
    out+=text(48,48,sid+' / COMPONENT DIAGRAM',14,SOFT,500)+text(48,84,'핵심 컴포넌트와 의존 관계',24,INK,600)
    for z in spec.get('zones',[]):
        out+=f'<rect x="{z["x"]}" y="{z["y"]}" width="{z["width"]}" height="{z["height"]}" rx="6" fill="none" stroke="{RULE}" stroke-dasharray="6,4"/>'
        out+=text(z['x']+16,z['y']+20,z['label'],12,SOFT)
    older=[]
    for e,path in zip(spec['edges'],paths):
        kind='replication' if e['kind']=='replication' else ('external' if any(n['id']==e['target'] and n['kind']=='external' for n in spec['nodes']) else 'dependency')
        color=ACCENT if kind=='replication' else (LINK if kind=='external' else MUTED)
        crossings=crossing_points(path,older);d=svg_path(path,crossings)
        dash='' if kind=='replication' else ' stroke-dasharray="6,4"'
        if crossings:out+=f'<path d="{d}" fill="none" stroke="{PAPER}" stroke-width="6"/>'
        points=' '.join(f'{x},{y}' for x,y in path)
        out+=f'<path data-role="connector" data-source="{e["source"]}" data-target="{e["target"]}" data-relation="{e["kind"]}" data-points="{points}" d="{d}" fill="none" stroke="{color}" stroke-width="1.5"{dash}/>'
        out+=arrowhead(path[-1],path[-2],color)
        older.append(path)
    out+=''.join(node_svg(n) for n in spec['nodes'])
    out+=f'<line x1="48" y1="664" x2="1232" y2="664" stroke="{RULE}"/>'
    out+=f'<path d="M 48 696 H 96" fill="none" stroke="{MUTED}" stroke-dasharray="6,4"/>'+arrowhead((96,696),(48,696),MUTED)
    out+=text(112,700,'사용하는 쪽 → 제공하는 쪽',14,MUTED)
    if any(e['kind']=='replication' for e in spec['edges']):
        out+=f'<path d="M 448 696 H 496" fill="none" stroke="{ACCENT}"/>'+arrowhead((496,696),(448,696),ACCENT)+text(512,700,'동기 복제 관계',14,MUTED)
    out+=text(1232,700,'상세 포트·인터페이스 생략',12,SOFT,400,'end')+'</svg>'
    return out


def build(root,strategies):
    specs=json.loads((root/'content/components.json').read_text(encoding='utf-8'))
    assert set(specs)==set(strategies),'Every strategy needs one component diagram'
    output=root/'site/components';output.mkdir(parents=True,exist_ok=True)
    figures={}
    css=f'''*{{box-sizing:border-box}}body{{margin:0;background:{PAPER};color:{INK};font:16px/1.8 {SANS}}}main{{max-width:1360px;margin:auto;padding:32px}}h1{{font:400 30px/1.5 'Instrument Serif','Noto Sans KR',serif;margin:0 0 20px}}figure{{margin:0}}.diagram-container{{width:100%;min-width:0}}svg{{display:block;width:100%;max-width:100%;min-width:0;height:auto}}figcaption{{margin:20px 0;max-width:1080px;font-size:14px;color:{MUTED}}}@media(max-width:600px){{main{{padding:16px}}h1{{font-size:22px}}}}@media print{{main{{padding:0}}figure{{break-inside:avoid}}}}'''
    for sid,spec in specs.items():
        svg=render(sid,spec);note=spec['note'];figures[sid]=dict(svg=svg,note=note)
        title=sid+' '+strategies[sid]['title']+' · Component Diagram'
        html=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><link rel="stylesheet" href="{escape(FONT_URL,quote=True)}"><style>{css}</style></head><body><main><h1>{escape(title)}</h1><figure><div class="diagram-container">{svg}</div><figcaption>{escape(note)}</figcaption></figure></main></body></html>'
        (output/(sid.lower()+'.html')).write_text(html,encoding='utf-8')
    return figures
