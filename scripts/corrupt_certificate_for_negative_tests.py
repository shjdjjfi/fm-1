#!/usr/bin/env python3
"""Create intentionally invalid certificates for negative checker tests."""
import argparse, json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input'); p.add_argument('--kind', required=True, choices=['rule','substitution','side-condition','closing','initial','macro']); p.add_argument('--out', required=True)
args = p.parse_args()
data = json.loads(Path(args.input).read_text())
if args.kind == 'macro':
    data['macro_steps'][0]['rule_sequence'][0] = 'not_a_supported_rule'
elif args.kind == 'initial':
    data['initial_sequent'] += ' /* corrupted */'
elif data.get('steps'):
    step = data['steps'][-1] if args.kind in {'side-condition','closing'} else data['steps'][0]
    if args.kind == 'rule':
        step['rule'] = 'not_a_supported_rule'
    elif args.kind == 'substitution':
        step['substitution']['x'] = 42
    elif args.kind == 'side-condition':
        step['side_conditions'] = []
    elif args.kind == 'closing':
        step['branch_closed'] = True; step['after'] = 'not closed'
Path(args.out).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
