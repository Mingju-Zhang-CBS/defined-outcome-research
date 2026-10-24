import argparse
import json
from datetime import datetime, timezone
from .study import run
from .quotes import read_quotes


def main():
    parser=argparse.ArgumentParser(description="Issuer terms and declared model scenarios; no live feed")
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--demo',action='store_true')
    group.add_argument('--quotes',help='User-supplied licensed observation CSV; audited separately from marks')
    parser.add_argument('--output',default='local-runs/demo')
    parser.add_argument('--as-of',help='Timezone-aware audit timestamp; default current UTC')
    args=parser.parse_args()
    if args.demo:
        result=run(args.output)
        print(json.dumps({k:result[k] for k in ['data_kind','entry_scenarios','initial_costs','quote_observations']},indent=2))
    else:
        as_of=datetime.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc)
        print(json.dumps([q.summary(as_of) for q in read_quotes(args.quotes)],indent=2,allow_nan=False))


if __name__ == '__main__': main()
