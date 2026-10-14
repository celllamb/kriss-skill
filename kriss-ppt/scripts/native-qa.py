#!/usr/bin/env python3
import argparse,sys
from pathlib import Path
from qa_common import native_qa,html_qa,parity_qa,save
ap=argparse.ArgumentParser(description="Run native QA against captured .evidence; export first")
ap.add_argument('pptx',type=Path);ap.add_argument('--evidence',type=Path);a=ap.parse_args()
e=a.evidence or a.pptx.with_suffix('.evidence')
try:r=native_qa(a.pptx,e)
except Exception as err:r={'pass':False,'error':str(err)}
save(e/'native-qa.json',r);print('PASS' if r['pass'] else 'FAIL');sys.exit(0 if r['pass'] else 1)
