"""purpose: shared I/O for gates: read JSON input (file or '-'), print JSON result, return the exit code."""
import json
import sys


class UsageError(Exception):
    pass


def _no_constant(name):
    raise UsageError("%s is not allowed in gate input" % name)


def read_input(argv):
    if len(argv) != 2:
        raise UsageError("usage: %s INPUT.json|-" % argv[0])
    if argv[1] == "-":
        return json.load(sys.stdin, parse_constant=_no_constant)
    with open(argv[1], encoding="utf-8") as fh:
        return json.load(fh, parse_constant=_no_constant)


def finding(rule, message, where="", severity="fail"):
    return {"rule": rule, "severity": severity, "where": where, "message": message}


def emit(gate, findings, **extra):
    ok = not any(f["severity"] == "fail" for f in findings)
    print(json.dumps(dict({"gate": gate, "pass": ok, "findings": findings}, **extra), indent=1))
    return 0 if ok else 1


def run(gate, check, argv=None):
    """Call check(payload) -> (findings, extra). Exit 0 pass, 1 fail, 2 bad input."""
    argv = argv or sys.argv
    try:
        payload = read_input(argv)
        if not isinstance(payload, dict):
            raise UsageError("input must be a JSON object")
        findings, extra = check(payload)
    except (UsageError, OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"gate": gate, "pass": False, "error": str(e), "findings": []}))
        return 2
    return emit(gate, findings, **extra)
