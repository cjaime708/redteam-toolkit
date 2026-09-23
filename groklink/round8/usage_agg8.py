"""Aggregate token usage from PC-side turn-*.raw.json files for round 8.
Run on the PC via the file-daemon exec op. Prints JSON to stdout."""
import glob
import json
import os

ROOT = r"C:\Users\Owner\Documents\Muse-PC-Files\redteam\groklink"

def extract_usage(obj):
    """Try common usage layouts; return (in_tokens, out_tokens) or None."""
    if not isinstance(obj, dict):
        return None
    # direct usage dict
    for key in ("usage", "token_usage", "tokens"):
        u = obj.get(key)
        if isinstance(u, dict):
            inp = u.get("input_tokens", u.get("prompt_tokens", u.get("input")))
            out = u.get("output_tokens", u.get("completion_tokens", u.get("output")))
            if isinstance(inp, int) and isinstance(out, int):
                return inp, out
    # nested under response / result / data
    for key in ("response", "result", "data", "raw"):
        sub = obj.get(key)
        r = extract_usage(sub) if isinstance(sub, dict) else None
        if r:
            return r
    return None

per_case = {}
total_in = total_out = 0
files = 0
for case_dir in sorted(glob.glob(os.path.join(ROOT, "grok8_l12*"))):
    case = os.path.basename(case_dir)
    ci, co, n = 0, 0, 0
    for fp in sorted(glob.glob(os.path.join(case_dir, "turn-*.raw.json"))):
        try:
            obj = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        r = extract_usage(obj)
        if r:
            ci += r[0]
            co += r[1]
            n += 1
    per_case[case] = {"turns_with_usage": n, "in": ci, "out": co, "total": ci + co}
    total_in += ci
    total_out += co
    files += n

print(json.dumps({
    "per_case": per_case,
    "files_with_usage": files,
    "total_in": total_in,
    "total_out": total_out,
    "grand_total": total_in + total_out,
}))
