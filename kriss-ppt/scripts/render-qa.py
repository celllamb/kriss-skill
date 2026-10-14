#!/usr/bin/env python3
import argparse,sys
from pathlib import Path
from qa_common import native_qa,html_qa,parity_qa,save
ap=argparse.ArgumentParser(description="Run html QA against captured .evidence; export first")
ap.add_argument('pptx',type=Path);ap.add_argument('--evidence',type=Path);a=ap.parse_args()
e=a.evidence or a.pptx.with_suffix('.evidence')
try:r=html_qa(e)
except Exception as err:r={'pass':False,'error':str(err)}
save(e/'html-qa.json',r);print('PASS' if r['pass'] else 'FAIL');sys.exit(0 if r['pass'] else 1)
