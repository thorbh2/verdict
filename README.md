# Verdict

Verdict is a GenLayer prediction-market court for claims that need evidence, criteria, review, challenge, appeal, and final settlement. Users open markets, stake on YES or NO, attach resolution sources, and let an intelligent contract reason over the public record before funds are paid.

The repo is designed as a public proof package: frontend, contract source, deployment metadata, finalized smoke transactions, and test coverage are all included. Local wallet secrets are not.

## Live System

| Surface | Link |
| --- | --- |
| App | https://verdict-virid.vercel.app |
| GitHub | https://github.com/thorbh2/verdict |
| Contract | https://explorer-studio.genlayer.com/contracts/0x80E5C770869fe81317821b30b4a4b852A2D6DEc4 |
| Deploy tx | https://explorer-studio.genlayer.com/tx/0xecf51b800c11fd151ded138e12e98c2556fe017fb0c2c4fb27e1463278add64f |
| Vercel inspect | https://vercel.com/aspros-projects-07dbbeb8/verdict/Ds4mkiAT4mL7tSKcKc5zATqo3wWh |

## Why Verdict Exists

Most prediction demos stop at "create market, stake, resolve." Verdict extends that into a court-like lifecycle:

1. A market is created with a question, source URL, and scoring criteria.
2. Participants stake on YES or NO.
3. Evidence and obligations are attached to the case.
4. GenLayer reviews the claim against public sources.
5. A challenge window can be opened.
6. Challenges and appeals can be adjudicated with GenLayer reasoning.
7. Resolution, claim payout, and reputation recalculation are written on-chain.

The result is a prediction market that keeps the dispute record readable instead of hiding the important reasoning off-chain.

## Contract Architecture

| Area | Detail |
| --- | --- |
| Contract | `contracts/verdict_v2.py` |
| Size | 49,450 bytes |
| Network | GenLayer Studionet, chain id `61999` |
| Write methods | 30 |
| Read methods | 24 |
| GenLayer features | `gl.nondet.web.render`, `gl.nondet.exec_prompt`, `gl.eq_principle.prompt_comparative` |
| Storage model | markets, claims, evidence, obligations, reviews, challenges, appeals, stakes, reputation, audit events |
| Legacy UI support | `create_market`, `stake`, `resolve`, `claim`, `get_market`, `get_stake` |

Core lifecycle:

```text
set_claim_standard
  -> create_market
  -> add_obligation
  -> add_evidence
  -> stake YES / NO
  -> open_review
  -> review_claim_with_genlayer
  -> open_challenge_window
  -> submit_challenge
  -> resolve_challenge_with_genlayer
  -> submit_appeal
  -> resolve_appeal_with_genlayer
  -> resolve
  -> claim
  -> recalculate_reputation
```

Useful reads:

```text
get_market_count
get_market
get_claim_count
get_claim
get_item_count
get_item
get_stake_count
get_stake
```

## Verification Trail

The deployed contract was smoke-tested with 17 finalized writes, including three GenLayer reasoning calls and legacy frontend compatibility.

| Step | Transaction |
| --- | --- |
| Set market standard | https://explorer-studio.genlayer.com/tx/0x67d120c085b2f4da7332ef90376ff1c886ff4f579f100ba653f000a163a3293a |
| Create market | https://explorer-studio.genlayer.com/tx/0x7b6976ddb2cd9a67f369d93221028d482daede4d07e809ebbd475f50490642ff |
| Add obligation | https://explorer-studio.genlayer.com/tx/0x138f0ae462380e860d4f8b6d0e25068016eda0a4d579a95c94d53382fd9dc52e |
| Add docs evidence | https://explorer-studio.genlayer.com/tx/0xd73d1eca6d189c9d981728303c68ddfa5dcf47c8ba999581f1f7e61d12f44e1e |
| Add web evidence | https://explorer-studio.genlayer.com/tx/0x5cbb77444b9ec69cb8a1a066139b6db3096df631ed6ecba51fd5a42f6c7c9b24 |
| Stake YES | https://explorer-studio.genlayer.com/tx/0xc62ea2f686c077f3b6a0798378fefe128e4672383eead667bc34e01a91b61918 |
| Stake NO | https://explorer-studio.genlayer.com/tx/0xde4f7931c1f5b9b1a577b4a42929127290ce0407f32bd6d6c4c3c588c6244766 |
| GenLayer review | https://explorer-studio.genlayer.com/tx/0x86dcd0f9c554d12ae8e5b6ae81ca7caac788f606985aedfa0716cb78f04d2239 |
| Challenge resolution | https://explorer-studio.genlayer.com/tx/0x8fea2640e88986db4c1cbf680ee19c4b9b71b39a56e78f87641c150089a82cac |
| Appeal resolution | https://explorer-studio.genlayer.com/tx/0xaf4e2465eb8d6b660e8a29d5358332d68dddc6c8a84eb98c191cea8bdf661cfe |
| Resolve market | https://explorer-studio.genlayer.com/tx/0x82f21151398ef79aff35c17bf90c6b63149b1ea4d1c648f0edba9495d00197ed |
| Claim payout | https://explorer-studio.genlayer.com/tx/0xe721677b46f1846b31cf5ad4e16f680cdd55447e22c0e179a3318b7e33f613fa |

Test result:

```text
Schema valid
17 smoke writes finalized
23/23 read assertions passed
Static frontend repointed and Vercel-deployed
```

## Frontend

Verdict ships as a static market desk:

- newspaper/exchange-inspired market interface
- wallet connection through the bundled browser client
- GenLayer read calls through `genlayer-js`
- write actions routed through the connected EVM wallet
- standalone Vercel bundle with local `shared/` client files
- deployed contract address pinned in `app.js` and `deployment.json`

## Run Locally

From the private workspace:

```powershell
cd C:\Users\aspronim\Desktop\design-skills
npm run preview:start
npm run preview:project -- 01-verdict
```

Open:

```text
http://localhost:8080/01-verdict/
```

## Publish / Redeploy

```powershell
cd C:\Users\aspronim\Desktop\design-skills
npm run publish:project -- -Project 01-verdict -Repo https://github.com/thorbh2/verdict.git
```

Vercel production redeploy from the project folder:

```powershell
cd C:\Users\aspronim\Desktop\design-skills\projects\01-verdict
npx --yes vercel@latest --prod --yes
```

## Repository Safety

This public repository intentionally excludes local secrets:

- no private keys
- no vault files
- no `.env` files
- no `.vercel` project state
- no local dashboard data

Public files include only frontend code, contract source, deployment metadata, tests, and non-sensitive proof links.
