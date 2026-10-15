#!/usr/bin/env python3
"""Export explicit metre-based plan data as local OBJ proxies and SVG plan."""
import argparse
import hashlib
import json
import math
import re
from html import escape
from pathlib import Path


def number(value, label, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError(f'{label}: invalid finite numeric value')
    return float(value)


def vector(value, size, label):
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f'{label}: expected {size} coordinates')
    return [number(v,label) for v in value]


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}',value):
        raise ValueError('object id must use ASCII letters, digits, underscores or hyphens')
    return value


def box(name, center, size, direction=(1,0), material='wall'):
    dx,dy=direction
    vertices=[]
    for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
        along=x*size[0]/2
        across=y*size[1]/2
        vertices.append([center[0]+along*dx-across*dy,center[1]+along*dy+across*dx,center[2]+z*size[2]/2])
    return {'id':name,'vertices':vertices,'faces':[(1,4,3,2),(5,6,7,8),(1,2,6,5),(2,3,7,6),(3,4,8,7),(4,1,5,8)],'material':material,'volume':math.prod(size)}


def build_geometry(plan):
    if not isinstance(plan,dict) or plan.get('units')!='m':
        raise ValueError('plan must declare units=m')
    floor=plan['floor']
    width=number(floor['width'],'floor width',True)
    depth=number(floor['depth'],'floor depth',True)
    thickness=number(floor['thickness'],'floor thickness',True)
    # The floor slab is intentionally below z=0.
    objects=[box('Floor',[width/2,depth/2,-thickness/2],[width,depth,thickness],material='floor')]
    walls={}
    wall_list=plan.get('walls',[])
    if not isinstance(wall_list,list) or not wall_list or len(wall_list)>500:
        raise ValueError('provide 1-500 wall segments')
    for wall in wall_list:
        key=identifier(wall['id'])
        if key in walls or key=='Floor':
            raise ValueError('duplicate object id')
        start=vector(wall['start'],2,'wall start')
        end=vector(wall['end'],2,'wall end')
        if any(p[0]>width or p[1]>depth for p in (start,end)):
            raise ValueError('wall centerline outside plan footprint')
        length=math.dist(start,end)
        if length<1e-6:
            raise ValueError('zero-length wall')
        height=number(wall['height'],'wall height',True)
        thick=number(wall['thickness'],'wall thickness',True)
        direction=((end[0]-start[0])/length,(end[1]-start[1])/length)
        openings=[]
        entries=wall.get('openings',[])
        if not isinstance(entries,list) or len(entries)>50:
            raise ValueError('invalid opening list')
        for entry in entries:
            a=number(entry['offset'],'opening offset')
            b=a+number(entry['width'],'opening width',True)
            c=number(entry['bottom'],'opening bottom')
            d=c+number(entry['height'],'opening height',True)
            if b>length+1e-8 or d>height+1e-8:
                raise ValueError('opening exceeds wall bounds')
            if any(max(a,p[0])<min(b,p[1])-1e-8 and max(c,p[2])<min(d,p[3])-1e-8 for p in openings):
                raise ValueError('overlapping wall openings')
            openings.append((a,b,c,d))
        xs=sorted({0.,length}|{v for p in openings for v in p[:2]})
        zs=sorted({0.,height}|{v for p in openings for v in p[2:]})
        parts=[]
        for i,(a,b) in enumerate(zip(xs,xs[1:])):
            for j,(c,d) in enumerate(zip(zs,zs[1:])):
                u,z=(a+b)/2,(c+d)/2
                if b-a<=1e-8 or d-c<=1e-8 or any(p[0]<=u<=p[1] and p[2]<=z<=p[3] for p in openings):
                    continue
                center=[start[0]+u*direction[0],start[1]+u*direction[1],z]
                parts.append(box(f'{key}_{i}_{j}',center,[b-a,thick,d-c],direction))
        walls[key]=parts
        objects.extend(parts)
    furniture_ids=set()
    for entry in plan.get('furniture',[]):
        key=identifier(entry['id'])
        if key in walls or key in furniture_ids or key=='Floor' or any(part['id']==key for part in objects):
            raise ValueError('duplicate object id')
        center=vector(entry['center'],3,'furniture center')
        size=vector(entry['size'],3,'furniture size')
        if min(size)<=0 or center[2]-size[2]/2<0 or center[0]-size[0]/2<0 or center[0]+size[0]/2>width or center[1]-size[1]/2<0 or center[1]+size[1]/2>depth:
            raise ValueError('invalid furniture size or placement')
        furniture_ids.add(key)
        objects.append(box(key,center,size,material='furniture'))
    hidden=plan.get('cutaway_walls',[])
    if not isinstance(hidden,list) or any(key not in walls for key in hidden):
        raise ValueError('unknown cutaway wall')
    hidden_parts={part['id'] for key in hidden for part in walls[key]}
    cutaway=[part for part in objects if part['id'] not in hidden_parts]
    return objects,cutaway


def obj_text(objects):
    lines=['# Local metre-based proxy whitebox; z is up; no roof','mtllib materials.mtl']
    offset=0
    for part in objects:
        lines += [f'o {part["id"]}',f'usemtl {part["material"]}']
        lines += ['v '+' '.join(f'{v:.7f}' for v in point) for point in part['vertices']]
        lines += ['f '+' '.join(str(offset+v) for v in face) for face in part['faces']]
        offset+=8
    return '\n'.join(lines)+'\n'


def svg_plan(plan):
    width,depth=plan['floor']['width'],plan['floor']['depth']
    scale=min(1000/width,1000/depth)
    view_w,view_h=width*scale+80,depth*scale+130
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{view_w}" height="{view_h}" viewBox="0 0 {view_w} {view_h}">',
           '<rect width="100%" height="100%" fill="#f7f7f4"/>',
           f'<text x="40" y="30" font-family="sans-serif" font-size="18">{escape(plan.get("title","Local plan"))}</text>',
           f'<text x="40" y="55" font-family="sans-serif" font-size="12">Metre-based conceptual data; not a drawing reconstruction or compliance check</text>',
           f'<rect x="40" y="80" width="{width*scale}" height="{depth*scale}" fill="white" stroke="#999"/>']
    def point(p):
        return 40+p[0]*scale,80+(depth-p[1])*scale
    for wall in plan['walls']:
        x1,y1=point(wall['start']);x2,y2=point(wall['end'])
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#444" stroke-width="{wall["thickness"]*scale}"/>')
        length=math.dist(wall['start'],wall['end'])
        direction=[(wall['end'][i]-wall['start'][i])/length for i in range(2)]
        for opening in wall.get('openings',[]):
            a=[wall['start'][i]+opening['offset']*direction[i] for i in range(2)]
            b=[a[i]+opening['width']*direction[i] for i in range(2)]
            ax,ay=point(a);bx,by=point(b)
            lines.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{ "#dbe9fa" if opening["bottom"] else "white"}" stroke-width="{wall["thickness"]*scale}"/>')
    for furniture in plan.get('furniture',[]):
        c,s=furniture['center'],furniture['size']
        x,y=point([c[0]-s[0]/2,c[1]+s[1]/2])
        lines += [f'<rect x="{x}" y="{y}" width="{s[0]*scale}" height="{s[1]*scale}" fill="#ddd8cd" stroke="#888"/>',
                  f'<text x="{x+5}" y="{y+16}" font-size="12">{escape(furniture["id"])}</text>']
    return '\n'.join(lines+['</svg>'])


def export(plan_path, output):
    raw=plan_path.read_bytes()
    plan=json.loads(raw.decode('utf-8-sig'))
    full,cut=build_geometry(plan)
    if output.exists():
        raise ValueError('output directory exists; choose a new directory')
    output.mkdir(parents=True)
    (output/'full-walls.obj').write_text(obj_text(full),encoding='utf-8')
    (output/'cutaway.obj').write_text(obj_text(cut),encoding='utf-8')
    (output/'materials.mtl').write_text('newmtl wall\nKd 0.85 0.85 0.85\nnewmtl floor\nKd 0.70 0.70 0.70\nnewmtl furniture\nKd 0.92 0.90 0.85\n',encoding='utf-8')
    (output/'top-plan.svg').write_text(svg_plan(plan),encoding='utf-8')
    report={'status':'geometry_exported','units':'m','axes':'x-right,y-depth,z-up','input_sha256':hashlib.sha256(raw).hexdigest(),
            'full_objects':len(full),'cutaway_objects':len(cut),'full_vertices':8*len(full),'full_quad_faces':6*len(full),
            'assumptions':plan.get('assumptions',[]),'scope':'Explicit data converted to box-based mesh. No AI/CAD recognition, fine furniture, physical/engineering compliance or aesthetic acceptance.'}
    (output/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    try:
        print(json.dumps(export(args.plan,args.output),ensure_ascii=False))
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'status':'failed','error':str(exc)},ensure_ascii=False))
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
