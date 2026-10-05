# Milestone 3 — Public Testnet: Transaction Evidence

**Project Catalyst · Project 1400107 — Rolling Loans: Continuous Borrowing on Danogo**
**Milestone 3 — Public Testnet**
Milestone page → https://milestones.projectcatalyst.io/projects/1400107/milestones/3

**Rolling Loan** is called **Refinance via Dano** in the Danogo interface.

---

## Summary

| | |
|---|---|
| Network | Cardano **preprod** (public testnet) |
| Transactions | **261**, all confirmed on-chain |
| Wallet addresses | **62** |
| Blocks | 5,218,033 – 5,243,657 |
| Period | 2026-09-25 – 2026-10-02 (UTC) |
| Open | **131** |
| Refinance | **73** |
| Repay | **57** |

Every transaction links to its page on the preprod explorer:
`https://preprod.cardanoscan.io/transaction/<tx_hash>`.

---

## Acceptance criteria → evidence

| Criterion | Evidence |
|---|---|
| Loans can be opened, repaid or refinanced on testnet | 131 open, 73 refinance and 57 repay transactions, each confirmed on preprod — [`evidence/tx-classified.csv`](./evidence/tx-classified.csv) |
| Transactions are visible on a Cardano testnet explorer | Every row carries its preprod Cardanoscan link in the `explorer_url` column — [`evidence/tx-classified.csv`](./evidence/tx-classified.csv) |
| At least 50 wallets and 250 transactions | 62 wallet addresses, 261 transactions — [`evidence/wallets.txt`](./evidence/wallets.txt), [`evidence/tx-report.md`](./evidence/tx-report.md) |

---

## Feature usage per wallet

| Journeys performed by the wallet | Wallets |
|---|---|
| Open + Refinance + Repay | 22 |
| Open + Refinance | 39 |
| Open + Repay | 1 |
| **Total** | **62** |

Wallets that opened a loan: 62 · refinanced: 61 · repaid: 23.
Per-wallet transaction counts: [`evidence/tx-report.md`](./evidence/tx-report.md).

---

## How each transaction is classified

The journey is read from Danogo's own transaction memo (metadata label 674), and every transaction
of the same journey has the same on-chain shape:

| Memo (label 674) | Journey | Txs | Fluid pool in / out | Dano pool in / out | Mints | Burns | Example |
|---|---|---|---|---|---|---|---|
| `Dano Finance: Borrow from Fluid` | open | 131 | 1 / 1 | 0 / 2 | 3 | 0 | [`0869a547…`](https://preprod.cardanoscan.io/transaction/0869a547137b30d88e75ff6701dcc54f1d2f53727c79b1ec82ddec8e1e9e9a8c) |
| `Dano Finance: Create Loan` | refinance | 73 | 0 / 0 | 1 / 1 | 2 | 1 | [`8e06c071…`](https://preprod.cardanoscan.io/transaction/8e06c071bab3fcac48f60a34d3aa78d1d47d8325707c92992381dec50f5dea93) |
| `Dano Finance: Repay Fluid Loan` | repay | 57 | 0 / 0 | 1 / 1 | 0 | 1 | [`ddfbdd29…`](https://preprod.cardanoscan.io/transaction/ddfbdd29496383c64b5d8464312d22b0d2fdf88bc446c26677248e477c5a8c9c) |

Pool UTxOs are identified by script credential prefix: Fluid `338bb4e6`; Dano `cb972954`, `488ae61c`.
The per-transaction values are in [`evidence/tx-facts.csv`](./evidence/tx-facts.csv).

---

## Files

```
evidence/
  tx-report.md          per-wallet counts: open / refinance / repay
  tx-classified.csv     every transaction: wallet, block, time, memo, journey, explorer link
  tx-list.csv           every transaction: wallet, block, pools touched, explorer link
  tx-facts.csv          per-transaction on-chain facts used for classification
  koios-tx-info.jsonl   raw Koios preprod tx_info response, one transaction per line
  wallets.txt           the 62 wallet addresses
  SHA256SUMS            checksums of the six files above
scripts/
  koios_tx_facts.py     tx-list.csv -> koios-tx-info.jsonl, tx-facts.csv (Koios preprod)
  build_evidence.py     --classify: tx-facts.csv -> tx-classified.csv, tx-report.md, SHA256SUMS
```

---

## Verify

Python 3, standard library only. From the repository root:

```bash
(cd evidence && shasum -a 256 -c SHA256SUMS)
python3 scripts/koios_tx_facts.py
python3 scripts/build_evidence.py --classify
git status --short
```

Re-fetching from Koios reproduces `tx-facts.csv`, `tx-classified.csv` and `tx-report.md` byte for
byte. `koios-tx-info.jsonl` (and therefore `SHA256SUMS`) can differ only in the order Koios returns
each UTxO's `asset_list`; the content is identical.
