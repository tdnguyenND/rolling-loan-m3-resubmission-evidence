#!/usr/bin/env python3
"""Rebuild the derived evidence files.

  python3 scripts/build_evidence.py             source report + ledger -> tx-list.csv, wallets.txt
  python3 scripts/build_evidence.py --classify  tx-facts.csv -> tx-classified.csv, tx-report.md, SHA256SUMS
"""
import collections, csv, hashlib, json, re, sys
from pathlib import Path

E = Path("evidence")
JOURNEY = {
    "Dano Finance: Borrow from Fluid": "open",
    "Dano Finance: Create Loan": "refinance",
    "Dano Finance: Repay Fluid Loan": "repay",
}


def from_source():
    addr_of = {w["name"]: w["address"] for w in json.load(open("source/dano-preprod-txs.json"))["wallets"]}
    name, rows, wallets = None, [], []
    for line in open("source/TX-REPORT-261.md", encoding="utf8"):
        m = re.match(r"^(Generated-\d+)\s+—\s+\d+ tx", line)
        if m:
            name = m.group(1)
            wallets.append(addr_of[name])
            continue
        m = re.match(r"^(\d{7})\s+([0-9a-f]{64})\s+(Fluid\+Dano|Dano)\s+(\d{4}-\d\d-\d\d) (\d\d:\d\d)", line)
        if m:
            rows.append((addr_of[name], m.group(1), m.group(2), m.group(3), f"{m.group(4)}T{m.group(5)}:00Z"))
    rows.sort(key=lambda r: (int(r[1]), r[2]))
    assert len(rows) == len({r[2] for r in rows}), "duplicate tx hash"
    with open(E / "tx-list.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["wallet_address", "block", "tx_hash", "pools_touched", "utc_time_minute", "explorer_url"])
        for a, b, h, p, t in rows:
            w.writerow([a, b, h, p, t, "https://preprod.cardanoscan.io/transaction/" + h])
    (E / "wallets.txt").write_text("\n".join(wallets) + "\n")
    print(len(rows), "tx,", len(set(wallets)), "wallets")


def classify():
    facts = {r["tx_hash"]: r for r in csv.DictReader(open(E / "tx-facts.csv"))}
    rows = []
    for r in csv.DictReader(open(E / "tx-list.csv")):
        x = facts[r["tx_hash"]]
        memo = json.loads(x["memo_674"])["msg"][0]
        rows.append([r["wallet_address"], r["block"], r["tx_hash"], r["utc_time_minute"], memo,
                     JOURNEY.get(memo, "UNKNOWN: " + memo),
                     "https://preprod.cardanoscan.io/transaction/" + r["tx_hash"]])
    with open(E / "tx-classified.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["wallet_address", "block", "tx_hash", "utc_time_minute", "danogo_memo_674", "journey", "explorer_url"])
        w.writerows(rows)

    per, tot = collections.defaultdict(collections.Counter), collections.Counter()
    for r in rows:
        per[r[0]][r[5]] += 1
        tot[r[5]] += 1
    blocks = [int(r[1]) for r in rows]
    out = ["# Dano Preprod transactions, by wallet address", "",
           f"{len(rows)} transactions, {len(per)} wallets, blocks {min(blocks)}-{max(blocks)}, "
           f"{min(r[3] for r in rows)[:10]} to {max(r[3] for r in rows)[:10]} (UTC).",
           "Source: Koios preprod. Journey = Danogo's own memo (metadata label 674). Full list: `tx-classified.csv`.", "",
           f"Totals: open {tot['open']}, refinance {tot['refinance']}, repay {tot['repay']}.", "",
           "| Wallet address | Open | Refinance | Repay | Total |", "| --- | --- | --- | --- | --- |"]
    for a in sorted(per):
        c = per[a]
        out.append(f"| {a} | {c['open']} | {c['refinance']} | {c['repay']} | {sum(c.values())} |")
    (E / "tx-report.md").write_text("\n".join(out) + "\n")

    names = ["tx-report.md", "tx-list.csv", "tx-classified.csv", "tx-facts.csv", "koios-tx-info.jsonl", "wallets.txt"]
    (E / "SHA256SUMS").write_text(
        "".join(f"{hashlib.sha256((E / n).read_bytes()).hexdigest()}  {n}\n" for n in names))


if __name__ == "__main__":
    classify() if "--classify" in sys.argv else from_source()
