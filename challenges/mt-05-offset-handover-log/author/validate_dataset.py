#!/usr/bin/env python3
import argparse
import json
import tempfile
from pathlib import Path
from reference_solver import ROOT,unpack,solve
from independent_reference_solver import solve as independent

def validate(public):
    with tempfile.TemporaryDirectory() as tmp: result=solve(unpack(public,Path(tmp)))
    if result!=independent(public): raise ValueError('Independent intermediate values disagree')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('public',nargs='?',type=Path,default=ROOT/'public'); p.add_argument('--author-details',action='store_true'); a=p.parse_args()
    result=validate(a.public)
    print(json.dumps(result,sort_keys=True) if a.author_details else 'PASS: exactly one qualifying event; both solvers agree on all canonical intermediate values')
