"""Command-line entry point. All data acquisition is explicit."""
import argparse
import json
from pathlib import Path
from . import checkpoints, phishing, transients
from .data import fetch


def main():
    parser = argparse.ArgumentParser(description='Reproducible research baselines; no API keys needed')
    sub = parser.add_subparsers(dest='command', required=True)
    download = sub.add_parser('fetch')
    download.add_argument('project', choices=['phishing', 'checkpoints', 'transients', 'followup', 'all'])
    download.add_argument('--data', default='data/raw')
    run = sub.add_parser('run')
    run.add_argument('project', choices=['phishing', 'checkpoints', 'transients', 'all'])
    run.add_argument('--data', default='data/raw')
    run.add_argument('--output', default='results')
    run.add_argument('--seeds', nargs='+', type=int, default=[17, 42, 91])
    score = sub.add_parser('triage')
    score.add_argument('input', help='JSON containing text and citations: [{text: ...}]')
    score.add_argument('--threshold', type=float, default=.5)
    predict_parser = sub.add_parser('predict')
    predict_parser.add_argument('--model', required=True)
    predict_parser.add_argument('--input', required=True)
    predict_parser.add_argument('--output', required=True)
    predict_parser.add_argument('--trust-local-model', action='store_true')
    report_parser = sub.add_parser('report')
    report_parser.add_argument('--output', default='results')
    args = parser.parse_args()
    if args.command == 'report':
        from .report import generate
        print(generate(args.output))
        return
    if args.command == 'predict':
        from .inference import predict
        result = predict(args.model, args.input, args.output, args.trust_local_model)
        print(f'{len(result)} records scored into {args.output}')
        return
    if args.command == 'triage':
        if not 0 <= args.threshold <= 1:
            parser.error('threshold must be between 0 and 1')
        print(json.dumps(checkpoints.triage(json.loads(Path(args.input).read_text()), args.threshold), indent=2))
        return
    projects = ['phishing', 'checkpoints', 'transients'] if args.project == 'all' else [args.project]
    for project in projects:
        if args.command == 'fetch':
            print(json.dumps(fetch(project, args.data), indent=2))
        else:
            module = {'phishing': phishing, 'checkpoints': checkpoints, 'transients': transients}[project]
            result = module.run(args.data, args.output, tuple(args.seeds))
            print(f'{project}: {len(result["experiments"])} evaluations written to {args.output}')


if __name__ == '__main__':
    main()
