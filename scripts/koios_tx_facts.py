#!/usr/bin/env python3
"""Read-only: fetch Koios preprod tx_info for every hash in evidence/tx-list.csv.

Writes
  evidence/koios-tx-info.jsonl   raw Koios responses (one tx per line)
  evidence/tx-facts.csv          per-tx facts used to classify open / repay / refinance

Pool script credentials are matched by hex prefix (the report only keeps the first 8 chars).
Usage: python3 scripts/koios_tx_facts.py
"""
import csv, json, sys, time, urllib.request

API = "https://preprod.koios.rest/api/v1/tx_info"
POOLS = {"338bb4e6": "fluid", "cb972954": "dano_a", "488ae61c": "dano_b"}
BATCH = 25

hashes = [r["tx_hash"] for r in csv.DictReader(open("evidence/tx-list.csv"))]


def post(batch):
    body = json.dumps({"_tx_hashes": batch, "_inputs": True, "_metadata": True, "_assets": True,
                       "_scripts": True, "_withdrawals": False, "_certs": False}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(API, body, {"content-type": "application/json", "accept": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:  # network / 429
            print("retry", attempt, e, file=sys.stderr)
            time.sleep(2 ** attempt)
    sys.exit("koios unreachable")


def pool_of(cred):
    return POOLS.get((cred or "")[:8])


raw = {}
for i in range(0, len(hashes), BATCH):
    for tx in post(hashes[i:i + BATCH]):
        raw[tx["tx_hash"]] = tx
    print(f"{min(i + BATCH, len(hashes))}/{len(hashes)}", file=sys.stderr)

with open("evidence/koios-tx-info.jsonl", "w") as f:
    for h in hashes:
        if h in raw:
            f.write(json.dumps(raw[h], sort_keys=True) + "\n")

cols = ["tx_hash", "block_height", "found", "fluid_in", "fluid_out", "dano_in", "dano_out",
        "mints", "burns", "redeemers", "memo_674", "tx_error_hint"]
with open("evidence/tx-facts.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for h in hashes:
        tx = raw.get(h)
        if not tx:
            w.writerow([h, "", "no"] + [""] * 8)
            continue
        c = {"fluid_in": 0, "fluid_out": 0, "dano_in": 0, "dano_out": 0}
        for side, key in (("inputs", "in"), ("outputs", "out")):
            for u in tx.get(side) or []:
                p = pool_of((u.get("payment_addr") or {}).get("cred"))
                if p:
                    c[("fluid_" if p == "fluid" else "dano_") + key] += 1
        am = tx.get("assets_minted") or []
        mints = sum(1 for a in am if int(a["quantity"]) > 0)
        burns = sum(1 for a in am if int(a["quantity"]) < 0)
        pc = tx.get("plutus_contracts") or []
        memo = ((tx.get("metadata") or {}).get("674") or {})
        w.writerow([h, tx.get("block_height"), "yes", c["fluid_in"], c["fluid_out"], c["dano_in"], c["dano_out"],
                    mints, burns, len(pc), json.dumps(memo, ensure_ascii=False) if memo else "", ""])
print("done", len(raw), "of", len(hashes), file=sys.stderr)
