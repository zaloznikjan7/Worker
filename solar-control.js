import axios from "axios";
import { Ewelink } from "ewelink-api";
import { config } from "dotenv";

config();

async function main() {
  const now = new Date();
  const h = now.getUTCHours();
  if (h < 11 || h >= 19) {
    console.log(`Outside 11–19 UTC (${h}). Exiting.`);
    return;
  }

  // ── 1) Get SolarEdge data ────────────────────────────────
  const solaredgeUrl = process.env.SOLAREDGE_URL;
  const solaredgeCookie = process.env.SOLAREDGE_COOKIE;
  const { data } = await axios.get(solaredgeUrl, {
    headers: { 
      Cookie: solaredgeCookie,
      Accept: "application/json"
    }
  });

  const load     = parseFloat(data.load.currentPower);
  const pvPower  = parseFloat(data.pv.currentPower);
  console.log(`Grid load=${load}, PV power=${pvPower}`);

  // ── 2) Compute stage ─────────────────────────────────────
  // stage 0: grid <7  → turn both off 
  // stage 1: grid>7 & pv<9 → turn ch1 off, ch2 on  
  // stage 2: pv>=9 → turn both on
  let stage = 0;
  if (load > 7 && pvPower < 9) stage = 1;
  if (pvPower >= 9) stage = 2;
  console.log(`→ desired stage=${stage}`);

  // ── 3) Talk to eWeLink ───────────────────────────────────
  const conn = new Ewelink({
    email:       process.env.EWELINK_EMAIL,
    password:    process.env.EWELINK_PASSWORD,
    region:      process.env.EWELINK_REGION,
    APP_ID:      process.env.EWELINK_APP_ID,
    APP_SECRET:  process.env.EWELINK_APP_SECRET
  });

  const devices = await conn.getDevices();
  const deviceid = devices[0].deviceid;

  async function ensure(channel, desiredState) {
    const st = await conn.getDevicePowerState(deviceid, channel);
    if (st.state !== desiredState) {
      console.log(`Channel${channel}: ${st.state} → toggling to ${desiredState}`);
      await conn.setDevicePowerState(deviceid, "toggle", channel);
    } else {
      console.log(`Channel${channel} already ${desiredState}`);
    }
  }

  // stage→desired states
  await ensure(1, (stage === 2) ? "on" : "off");
  await ensure(2, (stage >= 1)  ? "on" : "off");
}

main().catch(err => {
  console.error("Fatal error:", err);
  process.exit(1);
});
