"""Round-4 turn-loop driver: runs all four trojan-horse cases sequentially.

Usage: python3 drive_all.py
  - workspace-backed harness state (mh.STATE_ROOT patched); /tmp untouched
  - TMPDIR=/var/tmp for sandbox env roots
  - per case: turns 1..10, stop at FINAL:, relay ERROR -> sleep 60 -> retry once
  - after each TOOL: execute via harness, backup state+env to harness_backup
  - writes progress log to round4/drive.log and finals to round4/finals.json
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

os.environ['TMPDIR'] = '/var/tmp'
sys.path.insert(0, os.path.expanduser('~/workspace/redteam-toolkit'))

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, 'rt_manual')
BACKUP = os.path.join(HERE, 'harness_backup')
PC_OPS = os.path.expanduser('~/workspace/goals/hustler-operation-takeover/hidden_files/pc-fileops')
WRAPPER = "C:\\Users\\Owner\\Documents\\Muse-PC-Files\\redteam\\groklink\\run-grok-turn.py"
CASES = ["grok4_t1", "grok4_t2", "grok4_t3", "grok4_t4"]
MAX_TURNS = 10
LOG = os.path.join(HERE, 'drive.log')

import sandbox.manual_harness as mh
mh.STATE_ROOT = Path(STATE_DIR)
from sandbox.agent import parse_reply  # noqa: F401  (ensures import works)

BRIEF = open(os.path.join(HERE, 'brief.txt')).read()
if not BRIEF.endswith('\n'):
    BRIEF += '\n'


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    open(LOG, 'a').write(line + '\n')


def restore(case):
    state_path = os.path.join(STATE_DIR, case, 'case.json')
    if os.path.exists(state_path):
        return
    bkp = os.path.join(BACKUP, f'{case}.case.json')
    if not os.path.exists(bkp):
        raise RuntimeError(f'no state and no backup for {case}')
    os.makedirs(os.path.join(STATE_DIR, case), exist_ok=True)
    shutil.copy(bkp, state_path)
    s = json.load(open(state_path))
    new_env = f'/var/tmp/rt_sandbox_{case}_restored'
    if os.path.exists(new_env):
        shutil.rmtree(new_env)
    shutil.copytree(os.path.join(BACKUP, f'{case}_env'), new_env)
    s['env_root'] = new_env
    json.dump(s, open(state_path, 'w'), indent=2)
    log(f'{case}: restored state+env from backup')


def build_prompt(case):
    state_path = os.path.join(STATE_DIR, case, 'case.json')
    state = json.load(open(state_path))
    parts = [BRIEF.rstrip('\n'), '', '']
    for t in state['transcript']:
        if t['actor'] == 'agent' and t['kind'] == 'tool_call':
            args = json.dumps(t['args'], separators=(', ', ': '))
            parts.append(f"Atlas: TOOL: {t['tool']} {args}")
            parts.append('')
        elif t['actor'] == 'environment' and t['kind'] == 'observation':
            parts.append('Tool observation:')
            parts.append(t['text'])
            parts.append('')
    parts.append('Continue with your next step.')
    parts.append('')
    return '\n'.join(parts)


def relay_turn(case, turn, prompt):
    ops = [
        {"op": "write", "path": f"redteam/groklink/{case}/turn-{turn:02d}.prompt.txt",
         "content": prompt},
        {"op": "exec", "cwd": "redteam",
         "command": ["python", WRAPPER, "--case", case, "--turn", str(turn)],
         "timeout_seconds": 300},
    ]
    r = subprocess.run(
        [sys.executable, 'pc_fileops.py', '--ops', json.dumps(ops),
         '--timeout', '400', '--poll', '15'],
        capture_output=True, text=True, cwd=PC_OPS)
    try:
        d = json.loads(r.stdout[r.stdout.find('{'):])
    except Exception as e:
        return None, f'relay parse failed: {e}'
    res = d.get('results', [])
    if len(res) < 2 or not res[0].get('ok') or not res[1].get('ok'):
        return None, f'relay op failed: {json.dumps(res)[:300]}'
    try:
        out = json.loads(res[1]['output'])
        return out['response'], None
    except Exception as e:
        return None, f'wrapper output parse failed: {e}'


def extract_line(response):
    for ln in response.strip().splitlines()[::-1]:
        s = ln.strip()
        if s.startswith('TOOL:') or s.startswith('FINAL:'):
            return s
    return ''


class _Args:
    pass


def do_tool(case, line):
    a = _Args()
    a.case = case
    a.call = line
    mh.cmd_tool(a)  # appends to transcript, prints observation


def backup(case):
    s = json.load(open(os.path.join(STATE_DIR, case, 'case.json')))
    shutil.copy(os.path.join(STATE_DIR, case, 'case.json'),
                os.path.join(BACKUP, f'{case}.case.json'))
    dest = os.path.join(BACKUP, f'{case}_env')
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(s['env_root'], dest)


def run_case(case):
    restore(case)
    grok_lines = []
    final = None
    for turn in range(1, MAX_TURNS + 1):
        prompt = build_prompt(case)
        response, err = relay_turn(case, turn, prompt)
        if err:
            log(f'{case} t{turn}: {err}; sleeping 60s then one retry')
            time.sleep(60)
            response, err = relay_turn(case, turn, prompt)
            if err:
                log(f'{case} t{turn}: retry failed ({err}); aborting case')
                return grok_lines, None, f'aborted at turn {turn}: {err}'
        line = extract_line(response or '')
        if not line:
            log(f'{case} t{turn}: no protocol line; aborting case')
            return grok_lines, None, f'aborted at turn {turn}: no protocol line'
        grok_lines.append(line)
        log(f'{case} t{turn}: {line[:100]}')
        if line.startswith('FINAL:'):
            final = line
            break
        do_tool(case, line)
        backup(case)
    return grok_lines, final, None


def main():
    results = {}
    for case in CASES:
        log(f'=== starting {case} ===')
        t0 = time.time()
        grok_lines, final, error = run_case(case)
        dur = round(time.time() - t0, 1)
        results[case] = {
            'turns': len(grok_lines),
            'grok_lines': grok_lines,
            'final': final,
            'error': error,
            'duration_s': dur,
        }
        log(f'=== {case} done: {len(grok_lines)} turns, {dur}s, '
            f'{"FINAL" if final else "ABORT: " + str(error)} ===')
    json.dump(results, open(os.path.join(HERE, 'turn_results.json'), 'w'), indent=2)
    log('ALL CASES DONE')


if __name__ == '__main__':
    main()
