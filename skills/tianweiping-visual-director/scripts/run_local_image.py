#!/usr/bin/env python3
"""Preflight and optionally run a native-node workflow on local ComfyUI only."""
import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

NATIVE={'UNETLoader','DualCLIPLoader','VAELoader','CLIPTextEncode','FluxGuidance','EmptyLatentImage','KSampler','VAEDecode','SaveImage','CheckpointLoaderSimple','VAEEncode','LoadImage','BasicGuider','RandomNoise','KSamplerSelect','BasicScheduler','SamplerCustomAdvanced'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('redirects are not permitted by this local-only client')


def endpoint(value):
    parsed=urllib.parse.urlsplit(value)
    if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.path not in {'','/'} or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError('endpoint must be the root of a local HTTP ComfyUI service')
    return value.rstrip('/')


def graph(value):
    if isinstance(value,dict) and isinstance(value.get('prompt'),dict):
        value=value['prompt']
    if not isinstance(value,dict) or not value or 'nodes' in value:
        raise ValueError('export a ComfyUI API prompt graph, not an editor workflow')
    for key,node in value.items():
        if not isinstance(key,str) or not isinstance(node,dict) or node.get('class_type') not in NATIVE or not isinstance(node.get('inputs'),dict):
            raise ValueError('only explicitly supported native local nodes are accepted')
        for item in node['inputs'].values():
            if isinstance(item,list) and len(item)==2 and isinstance(item[0],str) and type(item[1]) is int:
                if item[0] not in value or item[1]<0:
                    raise ValueError('invalid node link')
            if isinstance(item,str) and '://' in item:
                raise ValueError('remote input strings are not accepted')
    if not any(node['class_type']=='SaveImage' for node in value.values()):
        raise ValueError('workflow needs a SaveImage output')
    return value


def client(base):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def request(path,payload=None,binary=False):
        data=json.dumps(payload).encode() if payload is not None else None
        req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'} if data else {})
        with opener.open(req,timeout=30) as response:
            content=response.read()
        return content if binary else json.loads(content)
    return request


def preflight(prompt,request):
    request('/system_stats')
    for name in sorted({node['class_type'] for node in prompt.values()}):
        info=request('/object_info/'+urllib.parse.quote(name))
        if name not in info:
            raise ValueError('node not available on this service: '+name)
        required=info[name].get('input',{}).get('required',{})
        optional=info[name].get('input',{}).get('optional',{})
        for node in (n for n in prompt.values() if n['class_type']==name):
            if any(key not in node['inputs'] for key in required):
                raise ValueError('missing required input for '+name)
            for key,value in node['inputs'].items():
                descriptor=(required|optional).get(key)
                if descriptor is None:
                    raise ValueError('unsupported input '+name+'.'+key)
                if isinstance(value,list):
                    continue
                if isinstance(descriptor[0],list) and value not in descriptor[0]:
                    raise ValueError('unavailable model or enum value for '+name+'.'+key)
    queue=request('/queue')
    return {'status':'preflight_pass','running':len(queue.get('queue_running',[])),'pending':len(queue.get('queue_pending',[]))}


def wait_result(record,output,request,seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        history=request('/history/'+urllib.parse.quote(record['prompt_id']))
        result=history.get(record['prompt_id'])
        if result:
            status=result.get('status',{})
            if status.get('status_str')=='error':
                record.update(status='generation_failed',server_messages=status.get('messages',[]))
                break
            images=[image for node in result.get('outputs',{}).values() for image in node.get('images',[])]
            if images:
                paths=[]
                for i,item in enumerate(images):
                    data=request('/view?'+urllib.parse.urlencode({k:item.get(k,'') for k in ('filename','subfolder','type')}),binary=True)
                    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                        raise ValueError('expected a PNG result from SaveImage')
                    path=output/f'image_{i+1:02}.png'
                    if path.exists():
                        if path.read_bytes()!=data:
                            raise ValueError('existing result differs; preserve it and use another output location')
                    else:
                        with path.open('xb') as stream:
                            stream.write(data)
                    paths.append({'path':str(path.resolve()),'sha256':hashlib.sha256(data).hexdigest()})
                record.update(status='media_created_pending_review',images=paths)
                break
            if status.get('completed'):
                record.update(status='completed_without_image')
                break
        time.sleep(2)
    record.setdefault('status','pending')
    (output/'request.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workflow',type=Path)
    parser.add_argument('--endpoint',default='http://127.0.0.1:8188')
    parser.add_argument('--submit',action='store_true')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--wait',type=int,default=240)
    parser.add_argument('--resume',type=Path,help='Resume an existing request.json; never submit again')
    args=parser.parse_args()
    try:
        if args.wait<1 or args.wait>3600:
            raise ValueError('wait must be between 1 and 3600 seconds')
        request=client(endpoint(args.endpoint))
        if args.resume:
            record=json.loads(args.resume.read_text(encoding='utf-8-sig'))
            if record.get('endpoint')!=endpoint(args.endpoint):
                raise ValueError('resume endpoint differs from the saved request')
            if record.get('images'):
                print(json.dumps(record,ensure_ascii=False));return 0
            record.pop('status',None)
            result=wait_result(record,args.resume.parent,request,args.wait)
        else:
            raw=args.workflow.read_bytes()
            prompt=graph(json.loads(raw.decode('utf-8-sig')))
            info=preflight(prompt,request)
            if not args.submit:
                print(json.dumps(info,ensure_ascii=False));return 0
            if info['running'] or info['pending']:
                raise ValueError('service has other queued work; no task submitted')
            if args.output is None or args.output.exists():
                raise ValueError('submit requires a new output directory')
            args.output.mkdir(parents=True)
            record={'endpoint':endpoint(args.endpoint),'workflow_sha256':hashlib.sha256(raw).hexdigest(),'submitted_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
            submitted=request('/prompt',{'prompt':prompt,'client_id':'tian-weiping-local-visual'})
            if submitted.get('node_errors') or not submitted.get('prompt_id'):
                raise ValueError('service did not accept the workflow')
            record['prompt_id']=submitted['prompt_id']
            (args.output/'request.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            result=wait_result(record,args.output,request,args.wait)
        print(json.dumps(result,ensure_ascii=False))
        return 0 if result.get('status')=='media_created_pending_review' else 3
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'status':'failed_or_unavailable','error':str(exc)},ensure_ascii=False))
        return 1

if __name__=='__main__':
    raise SystemExit(main())
