"""Build the next Groklink turn prompt from local harness state.

Usage: python3 build_prompt.py <case> > <outfile>

Format matches round 2 exactly:
  <brief>

  Atlas: TOOL: <name> <json args>

  Tool observation:
  <observation text>

  ... repeated per turn ...

  Continue with your next step.

Reads brief from the sibling brief.txt and harness state from
/tmp/rt_manual/<case>/case.json. If /tmp was wiped, restore from
~/workspace/redteam-toolkit/groklink/round3/harness_backup/ first.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
case = sys.argv[1]
brief = open(os.path.join(HERE, 'brief.txt')).read()
if not brief.endswith('\n'):
    brief += '\n'
state_path = f'/tmp/rt_manual/{case}/case.json'
if not os.path.exists(state_path):
    sys.stderr.write(f'NO STATE at {state_path}; restore from harness_backup first\n')
    sys.exit(2)
state = json.load(open(state_path))

parts = [brief.rstrip('\n'), '', '']
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
sys.stdout.write('\n'.join(parts))
