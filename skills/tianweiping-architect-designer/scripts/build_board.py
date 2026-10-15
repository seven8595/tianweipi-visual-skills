#!/usr/bin/env python3
"""Render a source-labelled, embedded-image SVG board without external requests."""
import argparse
import base64
import hashlib
import json
import re
from html import escape
from pathlib import Path


def build(data, base):
    if not isinstance(data,dict) or data.get('mode') not in ('project','research'):
        raise ValueError('mode must be project or research')
    title=data.get('title')
    if not isinstance(title,str) or not title.strip():
        raise ValueError('nonempty title required')
    cards=data.get('cards')
    if not isinstance(cards,list) or not 1<=len(cards)<=24:
        raise ValueError('provide 1-24 cards')
    if data['mode']=='project' and len({c.get('scene_id') for c in cards})!=1:
        raise ValueError('project board cannot mix different scenes')
    labels=set()
    images=[]
    for card in cards:
        for key in ('id','label','scene_id','path'):
            if not isinstance(card.get(key),str) or not card[key].strip():
                raise ValueError(f'card {key} required')
        if card['id'] in labels:
            raise ValueError('duplicate card id')
        labels.add(card['id'])
        if '://' in card['path'] or card['path'].startswith(('\\\\','//')):
            raise ValueError('only local file paths supported')
        path=(base/card['path']).resolve()
        raw=path.read_bytes()
        if raw.startswith(b'\x89PNG\r\n\x1a\n'):
            mime='image/png'
        elif raw.startswith(b'\xff\xd8\xff'):
            mime='image/jpeg'
        else:
            raise ValueError('board inputs must be PNG or JPEG files')
        if len(raw)>20*1024*1024:
            raise ValueError('source image too large for a portable embedded board')
        images.append((card,mime,base64.b64encode(raw).decode('ascii'),hashlib.sha256(raw).hexdigest()))
    colors=data.get('palette',[])
    if not isinstance(colors,list) or any(not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color) for color in colors):
        raise ValueError('palette values must be six-digit hex colours')
    cols=3
    rows=(len(cards)+cols-1)//cols
    width,height=1440,170+rows*490+100
    banner='研究参考｜各图保留独立来源，不代表同一空间' if data['mode']=='research' else '项目草稿｜布局生成不等于品牌或艺术验收'
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#f6f4ef"/>',
           f'<text x="40" y="56" font-family="Microsoft YaHei,sans-serif" font-size="30" fill="#222">{escape(title)}</text>',
           f'<text x="40" y="94" font-family="Microsoft YaHei,sans-serif" font-size="18" fill="#666">{banner}</text>']
    for i,color in enumerate(colors):
        lines.append(f'<rect x="{40+i*86}" y="116" width="72" height="24" fill="{color}"/>')
    for i,(card,mime,encoded,digest) in enumerate(images):
        x,y=40+(i%cols)*465,170+(i//cols)*490
        lines += [f'<rect x="{x}" y="{y}" width="435" height="460" fill="white"/>',
                  f'<image x="{x+10}" y="{y+10}" width="415" height="380" preserveAspectRatio="xMidYMid meet" href="data:{mime};base64,{encoded}"/>',
                  f'<text x="{x+12}" y="{y+420}" font-family="Microsoft YaHei,sans-serif" font-size="20">{escape(card["label"])}</text>',
                  f'<text x="{x+12}" y="{y+448}" font-family="sans-serif" font-size="12" fill="#777">{escape(card["id"]+" / "+card["scene_id"]+" / "+digest[:12])}</text>']
    lines += [f'<text x="40" y="{height-35}" font-family="Microsoft YaHei,sans-serif" font-size="14" fill="#666">本地排版；原图嵌入未做内容编辑。色块为指定版式参数，不是实测品牌色。</text>','</svg>']
    return '\n'.join(lines),{'status':'board_layout_built','mode':data['mode'],'cards':len(cards),'width':width,'height':height,'source_sha256':{card['id']:digest for card,mime,encoded,digest in images}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        data=json.loads(args.manifest.read_text(encoding='utf-8-sig'))
        svg,report=build(data,args.manifest.parent)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as stream:
            stream.write(svg)
        print(json.dumps(report,ensure_ascii=False))
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'status':'failed','error':str(exc)},ensure_ascii=False))
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
