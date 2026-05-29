#!/usr/bin/env python3
import subprocess, sys
cmd = ['./rustydl-cert', 'benchmark', '--out', sys.argv[1] if len(sys.argv) > 1 else 'results']
raise SystemExit(subprocess.call(cmd))
