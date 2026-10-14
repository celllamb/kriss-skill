#!/usr/bin/env python3
"""Release only after shared static, source coverage, reopen, native and parity gates."""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
import traceback
from pathlib import Path
from qa_common import native_qa, html_qa, parity_qa, regression_qa, save, sha
from validate_html import validate_file
from package_info import version_metadata


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('html',type=Path);ap.add_argument('pptx',type=Path,nargs='?')
    ap.add_argument('--baseline',type=Path);ap.add_argument('--allow-slides',default='');ap.add_argument('--chromium')
    args=ap.parse_args()
    html=args.html.resolve();pptx=(args.pptx or html.with_suffix('.pptx')).resolve()
    evidence=pptx.with_suffix('.evidence')
    final_html=html.with_name(html.stem+'.final.html')
    if pptx.suffix.lower()!='.pptx' or pptx in (html,final_html):
        ap.error('Output must be a .pptx path different from both source and final HTML')
    if args.baseline and args.baseline.resolve()==evidence:
        ap.error('Baseline evidence must not be the current output evidence directory')
    try:
        allowed={int(x) for x in args.allow_slides.split(',') if x.strip()}
        if any(x<1 for x in allowed):raise ValueError()
    except ValueError:
        ap.error('--allow-slides requires comma-separated positive slide numbers')
    if allowed and not args.baseline:
        ap.error('--allow-slides requires an explicit --baseline')
    evidence.mkdir(parents=True,exist_ok=True)
    report={}
    # Invalidate old success evidence immediately, even on a pre-export error.
    save(evidence/'manifest.json',{'schema':'kriss-ppt-evidence-v2','status':'BUILDING','input':str(html),'pptx':str(pptx)})
    save(evidence/'qa.json',{'status':'BUILDING'})
    try:
        identity=version_metadata()
        manifest=json.loads((evidence/'manifest.json').read_text())
        manifest.update(identity);save(evidence/'manifest.json',manifest)
        report['static']=validate_file(html)
        print('STATIC: '+('PASS' if report['static']['pass'] else 'FAIL'))
        if not report['static']['pass']:
            report['status']='BLOCKED';report['pptx_written']=False
        else:
            spec=importlib.util.spec_from_file_location('kriss_export',Path(__file__).with_name('export-pptx.py'))
            ex=importlib.util.module_from_spec(spec);spec.loader.exec_module(ex)
            ex.capture(html,pptx,args.chromium)
            for name,call in [('html',lambda:html_qa(evidence)),('native',lambda:native_qa(pptx,evidence)),('parity',lambda:parity_qa(pptx,evidence))]:
                try:report[name]=call()
                except Exception as error:report[name]={'pass':False,'error':str(error)}
                print(name.upper()+': '+('PASS' if report[name]['pass'] else 'FAIL'))
            if args.baseline:
                report['regression']=regression_qa(args.baseline.resolve(),evidence,allowed)
            report['status']='RELEASED' if all(v.get('pass',False) for v in report.values()) else 'BLOCKED'
            report['pptx_written']=True
    except Exception as error:
        report['status']='BUILD_ERROR';report['error']=str(error);traceback.print_exc()
    save(evidence/'qa.json',report)
    manifest=json.loads((evidence/'manifest.json').read_text())
    manifest['status']=report['status'];manifest['qa_sha256']=sha(evidence/'qa.json');save(evidence/'manifest.json',manifest)
    print(report['status']+': '+str(evidence/'qa.json'))
    return 0 if report['status']=='RELEASED' else 1


if __name__=='__main__':
    sys.exit(main())
