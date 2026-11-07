"""Stand-in for phpunit (PHP is not installed in the test bed): passes when every function the PHP tests call
is defined in src/*.php, so it fails on code without the change. Fixture only."""
import glob
import re
import sys

called = set()
for t in glob.glob("tests/*Test.php"):
    with open(t) as fh:
        called |= set(re.findall(r"\b(late_fee|invoice_total)\(", fh.read()))
defined = set()
for s in glob.glob("src/*.php"):
    with open(s) as fh:
        defined |= set(re.findall(r"function (\w+)\(", fh.read()))
missing = sorted(called - defined)
print("missing:", missing)
sys.exit(1 if missing else 0)
