#!/usr/bin/env python3
from pathlib import Path
from cert.stats import trusted_checker_loc
print(trusted_checker_loc([Path('checker')]))
