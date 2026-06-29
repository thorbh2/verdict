# Verdict V2

A GenLayer prediction-market court.

This repo packages the public casework UI and the GenLayer contract behind it: filings, evidence, review windows, challenge paths and final resolution.

## Verdict Brief

- Project folder: `projects/01-verdict`
- Frontend: static browser app
- Contract package: `contracts/` plus `deployment.json`
- Build status: Schema-valid (49450 bytes); clean deploy + 17 write smoke txs finalized incl 3 GenLayer reasoning calls; 23/23 read tests passed; app.js repointed.
- QA notes: Smoke: set standard, create market, add obligation, add two evidence records, stake YES/NO, review, challenge, appeal, resolve, claim and recalculate reputation. Legacy get_market/get_stake shape verified.

## Verdict On Studionet

- Network: studionet (61999)
- Contract: [0x80E5C770869fe81317821b30b4a4b852A2D6DEc4](https://explorer-studio.genlayer.com/contracts/0x80E5C770869fe81317821b30b4a4b852A2D6DEc4)
- Deploy tx: [0xecf51b80...add64f](https://explorer-studio.genlayer.com/tx/0xecf51b800c11fd151ded138e12e98c2556fe017fb0c2c4fb27e1463278add64f)
- Deployed at: 2026-06-24T03:07:58.292Z
- Smoke writes recorded: 17

## Adjudication Mechanics

- Primary source: `contracts/verdict_v2.py` (49,450 bytes)
- Public write/action methods: 30
- Read methods: 24
- GenLayer features: live web rendering, LLM adjudication, validator-comparative consensus, indexed storage, append-only collections

Typical flow: `create_market` -> `open_claim` -> `submit` -> `review` -> `resolve` -> `open_challenge_window` -> `submit_appeal` -> `set_claim_standard` -> `archive_claim`

Useful reads: `get_claim_count`, `get_market_count`, `get_claim`, `get_market`, `get_item_count`, `get_item`, `get_stake_count`, `get_stake`

The contract is deliberately larger than a one-method demo. It keeps lifecycle state, evidence records and read endpoints so the UI can show real project state instead of static copy.

## Run Verdict Locally

```powershell
cd C:\Users\aspronim\Desktop\design-skills
npm run preview:start
npm run preview:project -- 01-verdict
```

Open http://localhost:8080/01-verdict/.

## Smoke Transactions

- set_market_standard: [0x67d120c0...a3293a](https://explorer-studio.genlayer.com/tx/0x67d120c085b2f4da7332ef90376ff1c886ff4f579f100ba653f000a163a3293a)
- create_market: [0x7b6976dd...0642ff](https://explorer-studio.genlayer.com/tx/0x7b6976ddb2cd9a67f369d93221028d482daede4d07e809ebbd475f50490642ff)
- add_obligation: [0x138f0ae4...9dc52e](https://explorer-studio.genlayer.com/tx/0x138f0ae462380e860d4f8b6d0e25068016eda0a4d579a95c94d53382fd9dc52e)
- add_evidence_docs: [0xd73d1eca...f44e1e](https://explorer-studio.genlayer.com/tx/0xd73d1eca6d189c9d981728303c68ddfa5dcf47c8ba999581f1f7e61d12f44e1e)
- add_evidence_web: [0x5cbb7744...7c9b24](https://explorer-studio.genlayer.com/tx/0x5cbb77444b9ec69cb8a1a066139b6db3096df631ed6ecba51fd5a42f6c7c9b24)
- stake_yes: [0xc62ea2f6...b61918](https://explorer-studio.genlayer.com/tx/0xc62ea2f686c077f3b6a0798378fefe128e4672383eead667bc34e01a91b61918)
- stake_no: [0xde4f7931...244766](https://explorer-studio.genlayer.com/tx/0xde4f7931c1f5b9b1a577b4a42929127290ce0407f32bd6d6c4c3c588c6244766)
- open_review: [0x0fe0edb8...c9214e](https://explorer-studio.genlayer.com/tx/0x0fe0edb84047f760515f3c29e98f8b6c3d1378f0e4400199ef361c3fd2c9214e)

## Publish Verdict

```powershell
cd C:\Users\aspronim\Desktop\design-skills
npm run publish:project -- -Project 01-verdict -Repo https://github.com/aspro45/<repo-name>.git
```

Replace `<repo-name>` with the GitHub repository name before publishing.

## Keys And Boundaries

- Private keys and local vault files are not part of this repository.
- Public addresses, contract source, deployment metadata and frontend code are safe to publish.
- Vercel should receive only this project folder, never the workspace dashboard or vault data.
