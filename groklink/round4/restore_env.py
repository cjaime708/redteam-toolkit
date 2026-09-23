"""Restore round-4 sandbox envs after /var/tmp was wiped.

- t1/t3/t4: byte-restore from harness_backup/{case}_env (initial snapshots).
- t2: t3's snapshot is the same seed except email_002; overwrite email_002
  with T2_EMAIL2 extracted (via AST, no code execution) from setup_cases.py.
- Truncate t2's transcript to the 5 genuine turns (drop bogus turns 6-7
  recorded while env_root was missing).
- Seed harness_backup/grok4_t2_env so the watchdog has a restore source.
"""
import ast
import json
import os
import shutil

R4 = os.path.expanduser('~/workspace/redteam-toolkit/groklink/round4')
STATE = os.path.join(R4, 'rt_manual')
BACKUP = os.path.join(R4, 'harness_backup')


def get_t2_email2():
    src = open(os.path.join(R4, 'setup_cases.py')).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'T2_EMAIL2':
                    return ast.literal_eval(node.value)
    raise RuntimeError('T2_EMAIL2 not found')


def clear_and_copy(src, dst):
    os.makedirs(dst, exist_ok=True)
    for entry in os.listdir(dst):
        p = os.path.join(dst, entry)
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
    for entry in os.listdir(src):
        s = os.path.join(src, entry)
        d = os.path.join(dst, entry)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)


def env_root_of(case):
    return json.load(open(os.path.join(STATE, case, 'case.json')))['env_root']


# 1. t1 / t3 / t4 from their snapshots
for case in ('grok4_t1', 'grok4_t3', 'grok4_t4'):
    env_root = env_root_of(case)
    clear_and_copy(os.path.join(BACKUP, f'{case}_env'), env_root)
    print(f'{case}: restored {env_root}')

# 2. t2 from t3 snapshot + its own email_002
t2_root = env_root_of('grok4_t2')
clear_and_copy(os.path.join(BACKUP, 'grok4_t3_env'), t2_root)
t2_email2 = get_t2_email2()
with open(os.path.join(t2_root, 'inbox', 'email_002.txt'), 'w') as fh:
    fh.write(t2_email2)
print(f'grok4_t2: restored {t2_root} (t3 seed + T2_EMAIL2, {len(t2_email2)} chars)')

# 3. sanity checks (mirror setup_cases.py asserts)
for case in ('grok4_t1', 'grok4_t2', 'grok4_t3', 'grok4_t4'):
    root = env_root_of(case)
    assert os.path.isfile(os.path.join(root, 'inbox', 'email_001.txt')), case
    assert os.path.isfile(os.path.join(root, 'inbox', 'email_002.txt')), case
    assert os.path.isfile(os.path.join(root, 'vault', 'api_key.txt')), case
    assert os.path.isfile(os.path.join(root, 'notes', 'todo.txt')), case
    assert not os.path.exists(os.path.join(root, 'notes', 'backup_config.txt')), case
print('all envs pass sanity checks')

# 4. t2 transcript surgery: keep first 10 entries (5 genuine turns)
p = os.path.join(STATE, 'grok4_t2', 'case.json')
shutil.copy(p, p + '.pre-restore-bak')
s2 = json.load(open(p))
print('t2 transcript entries before:', len(s2['transcript']))
dropped = s2['transcript'][10:]
s2['transcript'] = s2['transcript'][:10]
json.dump(s2, open(p, 'w'), indent=2)
print('t2 transcript entries after:', len(s2['transcript']))
for t in dropped:
    if t['actor'] == 'agent':
        print('  dropped:', t['tool'], t['args'])

# 5. seed t2 env backup for the watchdog
dest = os.path.join(BACKUP, 'grok4_t2_env')
if os.path.exists(dest):
    shutil.rmtree(dest)
shutil.copytree(t2_root, dest)
print('seeded', dest)
print('RESTORE DONE')
