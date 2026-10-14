#!/usr/bin/env python3
"""Check release prerequisites without importing optional packages prematurely."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from package_info import version_metadata


def probe(chromium: str | None = None, fonts: list[str] | None = None) -> dict:
    report={'python':sys.version.split()[0], 'platform':platform.platform(), 'checks':[], 'fonts':[]}
    def check(name: str, ok: bool, **data):
        report['checks'].append({'name':name,'pass':ok,**data})
    try:
        report.update(version_metadata())
        check('Package VERSION',True,version=report['version'])
    except ValueError as error:
        check('Package VERSION',False,error=str(error))
    check('Python >=3.10',sys.version_info >= (3,10))
    packages={}
    for name in ('playwright','python-pptx','Pillow','numpy'):
        try:
            packages[name]=importlib.metadata.version(name)
            check(name,True,version=packages[name])
        except importlib.metadata.PackageNotFoundError:
            check(name,False,hint='python -m pip install -r requirements.txt')
    tools={}
    for name,aliases,args in [('LibreOffice',['libreoffice','soffice'],['--version']),
                             ('Poppler',['pdftoppm'],['-v']),('Fontconfig',['fc-match'],['-V'])]:
        exe=next((shutil.which(v) for v in aliases if shutil.which(v)),None)
        tools[name]=exe
        try:
            version=subprocess.run([exe,*args],capture_output=True,text=True,timeout=15) if exe else None
            check(name,bool(version and version.returncode==0),path=exe,
                  version=((version.stdout+version.stderr).strip().splitlines()[0] if version else None))
        except (OSError,subprocess.SubprocessError) as error:
            check(name,False,path=exe,error=str(error))
    node=shutil.which('node')
    report['optional_node']={'path':node,'required_for':'*.mjs authoring/CLI helpers only; Python release does not require Node'}
    browser_path=chromium or os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or shutil.which('chromium-browser')
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
            if browser_path:opts['executable_path']=browser_path
            browser=pw.chromium.launch(**opts)
            page=browser.new_page(viewport={'width':1280,'height':720})
            page.set_content('<p>KRISS browser probe</p>')
            ok=page.locator('p').inner_text()=='KRISS browser probe'
            session=page.context.new_cdp_session(page)
            session.send('DOMSnapshot.captureSnapshot',{'computedStyles':[],'includeDOMRects':True})
            check('Chromium + DOMSnapshot',ok,path=browser_path or 'Playwright-managed',version=browser.version)
            browser.close()
    except Exception as error:
        check('Chromium + DOMSnapshot',False,error=str(error),hint='python -m playwright install --with-deps chromium; or --chromium /path/to/browser')
    for font in fonts or []:
        try:
            result=subprocess.run([tools['Fontconfig'],'-f','%{family}',font],capture_output=True,text=True,check=True,timeout=15)
            resolved=result.stdout.strip()
            exact=font.casefold() in [v.strip().casefold() for v in resolved.split(',')]
            report['fonts'].append({'requested':font,'resolved':resolved,'pass':exact})
        except Exception as error:
            report['fonts'].append({'requested':font,'pass':False,'error':str(error)})
    report['pass']=all(v['pass'] for v in report['checks']) and all(v['pass'] for v in report['fonts'])
    report['scope']='Environment probe only, not slide certification or Microsoft PowerPoint validation.'
    return report


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--chromium');ap.add_argument('--font',action='append',default=[])
    ap.add_argument('--json',type=Path)
    args=ap.parse_args();result=probe(args.chromium,args.font)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(text,encoding='utf-8')
    print(text)
    return 0 if result['pass'] else 1

if __name__=='__main__':sys.exit(main())
