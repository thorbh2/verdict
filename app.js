import { makeReader, write, connectWallet, activeAccount, balanceOf, short, toGen, GEN, fmtErr }
  from "./shared/genlayer-lite.js";
import { icon, setIcons } from "./shared/icons.js";

const CONTRACT = "0x80E5C770869fe81317821b30b4a4b852A2D6DEc4";
const { read } = makeReader(CONTRACT);
const YES = 1, NO = 2;
let account = null, markets = [], detailSide = null;
const $ = (id) => document.getElementById(id);
const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

$("date").textContent = new Date().toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" });
$("contractFoot").innerHTML = `Contract ${short(CONTRACT)}`;
setIcons();

function toast(msg, kind = "", title = "wire") {
  const el = document.createElement("div"); el.className = "toast " + kind;
  el.innerHTML = `<span class="tt">${title}</span>`; el.appendChild(document.createTextNode(msg));
  $("log").appendChild(el); setTimeout(() => el.remove(), kind === "err" ? 16000 : 5200);
}

async function refreshWallet() {
  account = await activeAccount();
  const slot = $("walletslot");
  if (account) { let bal = 0n; try { bal = await balanceOf(account); } catch (_) {} slot.innerHTML = `<span class="mono" style="font-size:12px;color:var(--ink2)">${short(account)} · ${toGen(bal)} GEN</span>`; }
  else { slot.innerHTML = `<button class="btn sm" id="connectBtn">Connect<span class="ic">${icon("arrowRight")}</span></button>`; $("connectBtn").onclick = doConnect; }
}
async function doConnect() { try { account = await connectWallet(); toast("Connected on studionet.", "ok", "connected"); await refreshWallet(); } catch (e) { toast(fmtErr(e), "err", "wallet"); } }
async function ensureWallet() { if (!account) account = await connectWallet(); await refreshWallet(); }

const pct = (m) => { const y = Number(BigInt(m.yes_pool)), t = y + Number(BigInt(m.no_pool)); return t ? Math.round((y / t) * 100) : 50; };

async function load() {
  try {
    const count = Number(await read("get_market_count"));
    const out = [];
    for (let i = 0; i < count; i++) out.push({ id: i, ...(await read("get_market", [i])) });
    markets = out; render(); drawViz();
    $("mktmeta").textContent = count + (count === 1 ? " market" : " markets") + " on chain";
  } catch (e) { $("feed").innerHTML = `<div class="empty">Could not reach the ledger. ${fmtErr(e)}</div>`; drawViz(); }
}

// ---- D3 live odds visualization (real pools, or a calm demo wave when empty)
function drawViz() {
  const svg = d3.select("#oddsViz");
  svg.selectAll("*").remove();
  const W = 360, H = 220, m = { t: 10, r: 10, b: 26, l: 10 };
  let data = markets.filter((mk) => (Number(BigInt(mk.yes_pool)) + Number(BigInt(mk.no_pool))) > 0)
    .slice(-7).map((mk, i) => ({ label: "#" + mk.id, yes: pct(mk) }));
  if (!data.length) data = d3.range(7).map((i) => ({ label: "·" + (i + 1), yes: Math.round(50 + Math.sin(i * 0.9) * 22) }));

  const x = d3.scaleBand().domain(data.map((d) => d.label)).range([m.l, W - m.r]).padding(0.42);
  const y = d3.scaleLinear().domain([0, 100]).range([H - m.b, m.t]);

  // baseline 50% reference
  svg.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y(50)).attr("y2", y(50))
    .attr("stroke", "#c8bb9f").attr("stroke-dasharray", "3 4").attr("stroke-width", 1);
  svg.append("text").attr("x", W - m.r).attr("y", y(50) - 5).attr("text-anchor", "end")
    .attr("font-family", "JetBrains Mono, monospace").attr("font-size", 9).attr("fill", "#8a7d6b").text("50%");

  const g = svg.selectAll(".bar").data(data).enter().append("g");
  // NO portion (light, full height)
  g.append("rect").attr("x", (d) => x(d.label)).attr("y", m.t).attr("width", x.bandwidth())
    .attr("height", H - m.b - m.t).attr("rx", 4).attr("fill", "#eae3d2").attr("stroke", "#d8cdb6");
  // YES portion (ink, grows from bottom)
  g.append("rect").attr("x", (d) => x(d.label)).attr("width", x.bandwidth()).attr("rx", 4)
    .attr("y", H - m.b).attr("height", 0).attr("fill", "#191512")
    .transition().duration(900).delay((d, i) => i * 70).ease(d3.easeCubicOut)
    .attr("y", (d) => y(d.yes)).attr("height", (d) => (H - m.b) - y(d.yes));
  // YES % label
  g.append("text").attr("x", (d) => x(d.label) + x.bandwidth() / 2).attr("text-anchor", "middle")
    .attr("font-family", "JetBrains Mono, monospace").attr("font-size", 9.5).attr("fill", "#9c2a21").attr("font-weight", 600)
    .attr("y", (d) => y(d.yes) - 6).attr("opacity", 0).text((d) => Math.round(d.yes) + "%")
    .transition().duration(700).delay((d, i) => 400 + i * 70).attr("opacity", 1);
  // x labels
  g.append("text").attr("x", (d) => x(d.label) + x.bandwidth() / 2).attr("y", H - 8).attr("text-anchor", "middle")
    .attr("font-family", "JetBrains Mono, monospace").attr("font-size", 9).attr("fill", "#8a7d6b").text((d) => d.label);
}

function render() {
  const feed = $("feed");
  if (!markets.length) { feed.innerHTML = `<div class="empty">No markets yet. File the first one.</div>`; return; }
  feed.innerHTML = "";
  [...markets].reverse().forEach((mk) => {
    const st = Number(mk.status), yp = pct(mk);
    const stamp = st === 0 ? ["st-open", "Open"] : st === 1 ? ["st-res", Number(mk.outcome) === YES ? "Yes wins" : "No wins"] : ["st-void", "Void"];
    const card = document.createElement("div"); card.className = "market";
    card.innerHTML = `<div class="core">
      <span class="stamp ${stamp[0]}">${stamp[1]}</span>
      <h4 class="disp">${esc(mk.question)}</h4>
      <div class="src">SOURCE · ${esc(mk.resolution_url)}</div>
      <div class="odds-bar"><div class="odds-yes" style="width:0%">YES ${yp}%</div><div class="odds-no">${100 - yp}% NO</div></div>
      <div class="odds-legend"><span>${toGen(mk.yes_pool)} GEN</span><span>${toGen(mk.no_pool)} GEN</span></div>
      <div class="pot"><span class="g">Pot ${toGen((BigInt(mk.yes_pool) + BigInt(mk.no_pool)).toString())} GEN</span><span>${mk.stake_count} stakes · #${mk.id}</span></div>
    </div>`;
    card.onclick = () => openDetail(mk.id);
    feed.appendChild(card);
    requestAnimationFrame(() => { card.querySelector(".odds-yes").style.width = yp + "%"; });
  });
}

function openDrawer() { $("scrim").classList.add("on"); $("drawer").classList.add("on"); }
function closeDrawer() { $("scrim").classList.remove("on"); $("drawer").classList.remove("on"); }

function openCreate() {
  $("drawerTitle").textContent = "File a market";
  $("drawerBody").innerHTML = `
    <p style="color:var(--ink2);font-size:14.5px">Pose a yes/no question and name the page that will settle it.</p>
    <div class="fieldset"><span class="leg">The Question</span>
      <label>Question</label><input id="q" maxlength="160" placeholder="Will BTC close above $100k on Dec 31?" />
      <label>Resolution source URL</label><input id="url" placeholder="https://example.com/official-result" />
      <div class="hint">A stable public page that will plainly state the answer.</div></div>
    <div class="fieldset"><span class="leg">Resolution Rule</span>
      <label>How validators score the page</label><textarea id="crit" placeholder="YES if the page states the closing price is above 100000 USD."></textarea></div>
    <button class="btn ox block" id="createBtn">Publish market <span class="ic">${icon("arrowUpRight")}</span></button>`;
  $("createBtn").onclick = doCreate; openDrawer();
}

async function openDetail(id) {
  const mk = markets.find((x) => x.id === id); if (!mk) return;
  const st = Number(mk.status); detailSide = null;
  $("drawerTitle").textContent = "Market #" + id;
  let stakes = "";
  for (let i = 0; i < Number(mk.stake_count); i++) {
    try { const s = await read("get_stake", [id, i]); stakes += `<div class="subitem"><span>${short(s.backer)} · ${Number(s.side) === YES ? "YES" : "NO"}</span><span>${toGen(s.amount)} GEN${s.claimed ? " · claimed" : ""}</span></div>`; } catch (_) {}
  }
  const yp = pct(mk);
  let actions = "";
  if (st === 0) actions = `
    <div class="sidebtns"><div class="sidebtn" data-on="yes" id="sideYes">Back YES</div><div class="sidebtn" data-on="no" id="sideNo">Back NO</div></div>
    <label>Stake (GEN)</label><input id="stakeAmt" type="number" min="0" step="0.1" value="1" />
    <button class="btn block" id="stakeBtn" style="margin-top:14px">Place stake <span class="ic">${icon("arrowRight")}</span></button>
    <button class="btn ox block" id="resolveBtn" style="margin-top:10px">Resolve from web · AI consensus <span class="ic">${icon("spark")}</span></button>`;
  else actions = `<div class="verdict-banner ${st === 1 && Number(mk.outcome) === YES ? "vb-yes" : "vb-no"}">${st === 1 ? (Number(mk.outcome) === YES ? "Verdict · YES" : "Verdict · NO") : "Void · no clear answer"}</div>
    <label>Your stake # to ${st === 2 ? "reclaim" : "claim"}</label><input id="claimId" type="number" min="0" value="0" />
    <button class="btn block" id="claimBtn" style="margin-top:12px">${st === 2 ? "Reclaim stake" : "Claim winnings"} <span class="ic">${icon("arrowDown")}</span></button>`;
  $("drawerBody").innerHTML = `
    <div class="detail-q disp">${esc(mk.question)}</div>
    <div class="src" style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);margin-bottom:14px">SOURCE · <a href="${esc(mk.resolution_url)}" target="_blank" rel="noopener">${esc(mk.resolution_url)}</a></div>
    <div style="font-style:italic;color:var(--ink2);margin-bottom:14px">Rule: ${esc(mk.criteria) || "-"}</div>
    <div class="odds-bar"><div class="odds-yes" style="width:${yp}%">YES ${yp}%</div><div class="odds-no">${100 - yp}% NO</div></div>
    <div class="odds-legend" style="margin-bottom:6px"><span>${toGen(mk.yes_pool)} GEN YES</span><span>${toGen(mk.no_pool)} GEN NO</span></div>
    ${actions}
    ${stakes ? `<div style="margin-top:18px"><label>Ledger of stakes</label>${stakes}</div>` : ""}`;
  openDrawer();
  if (st === 0) { $("sideYes").onclick = () => pickSide("yes"); $("sideNo").onclick = () => pickSide("no"); $("stakeBtn").onclick = () => doStake(id); $("resolveBtn").onclick = () => doResolve(id); }
  else $("claimBtn").onclick = () => doClaim(id, st);
}
function pickSide(s) { detailSide = s; $("sideYes").classList.toggle("sel", s === "yes"); $("sideNo").classList.toggle("sel", s === "no"); }

async function doCreate() {
  const q = $("q").value.trim(), url = $("url").value.trim(), crit = $("crit").value.trim();
  if (!q) return toast("The question is required.", "err", "desk");
  if (!url) return toast("A resolution source URL is required.", "err", "desk");
  const btn = $("createBtn"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> publishing';
  try { await ensureWallet(); await write(CONTRACT, "create_market", [q, url, crit]); toast(`Market filed: "${q}"`, "ok", "published"); closeDrawer(); await load(); }
  catch (e) { toast(fmtErr(e), "err", "failed"); btn.disabled = false; btn.textContent = "Publish market"; }
}
async function doStake(id) {
  if (!detailSide) return toast("Pick YES or NO first.", "err", "stake");
  const amt = parseFloat($("stakeAmt").value); if (!(amt > 0)) return toast("Stake must be above zero.", "err", "stake");
  const btn = $("stakeBtn"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> staking';
  try { await ensureWallet(); await write(CONTRACT, "stake", [id, detailSide === "yes" ? YES : NO], GEN(amt)); toast(`Staked ${amt} GEN on ${detailSide.toUpperCase()}.`, "ok", "on-chain"); closeDrawer(); await load(); }
  catch (e) { toast(fmtErr(e), "err", "failed"); btn.disabled = false; btn.textContent = "Place stake"; }
}
async function doResolve(id) {
  if (!confirm("Resolve now? The contract reads the source page and validators must agree on the outcome. Calls a real LLM.")) return;
  const btn = $("resolveBtn"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> reading web · consensus';
  try { await ensureWallet(); toast("Validators are reading the source and agreeing on the truth…", "", "resolving"); await write(CONTRACT, "resolve", [id]); toast("Verdict reached on-chain.", "ok", "settled"); closeDrawer(); await load(); }
  catch (e) { toast(fmtErr(e), "err", "failed"); btn.disabled = false; btn.textContent = "Resolve from web"; }
}
async function doClaim(id, st) {
  const sid = parseInt($("claimId").value, 10); if (!(sid >= 0)) return toast("Enter a valid stake number.", "err", "claim");
  const btn = $("claimBtn"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> claiming';
  try { await ensureWallet(); await write(CONTRACT, "claim", [id, sid], 0n, "FINALIZED"); toast("Claim settled. Funds sent to your wallet.", "ok", "paid"); closeDrawer(); await load(); }
  catch (e) { toast(fmtErr(e), "err", "failed"); btn.disabled = false; btn.textContent = st === 2 ? "Reclaim stake" : "Claim winnings"; }
}

// Scroll reveals via IntersectionObserver (safe - CSS default is visible,
// .reveal adds entrance transition only when .in is applied, never stuck)
const _io = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting) { e.target.classList.add("in"); _io.unobserve(e.target); }
}), { threshold: 0.08 });
document.querySelectorAll(".reveal").forEach((el) => _io.observe(el));

$("fileBtn").onclick = openCreate;
$("refreshBtn").onclick = load;
$("closeDrawer").onclick = closeDrawer;
$("scrim").onclick = closeDrawer;
if (window.ethereum) window.ethereum.on?.("accountsChanged", refreshWallet);

refreshWallet();
load();
