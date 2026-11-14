"""Run with python -m src.citizen_audit.cli example.json"""
import json
import sys
from pathlib import Path
from .engine import audit_case

def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python -m src.citizen_audit.cli CASE.json')
    case = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    print(json.dumps(audit_case(case), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
