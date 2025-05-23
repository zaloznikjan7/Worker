import axios from "axios";
import Ewelink from "ewelink-api";
import { config } from "dotenv";

config();

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function checkAndToggle() {
  const now = new Date();
  const h = now.getUTCHours();

  // Only run between 11 ≤ UTC < 19
  if (h < 5 || h >= 17) {
    console.log(`Outside 9–17 UTC (hour=${h}) — sleeping only.`);
    return;
  }

  const solaredgeUrl    = process.env.SOLAREDGE_URL;
  const solaredgeToken = process.env.SOLAREDGE_TOKEN;
  const solaredgeClient = process.env.SOLAREDGE_CLIENT;
  const solaredgeRemmemberMeCookie = process.env.SOLAREDGE_CLIENT;
  const solaredgeSSO = process.env.SOLAREDGE_SSO;
  const solaredgeID = process.env.SOLAREDGE_ID;

  const cookieString = 
    `CSRF-TOKEN=${solaredgeToken}; ` +
    `SolarEdge_Client-1.6=${solaredgeToken} `; +
    'SolarEdge_Locale=en_US '; +
    `SolarEdge_SSO-1.4=${solaredgeSSO} `; +
    `SPRING_SECURITY_REMEMBER_ME_COOKIE=${SOLAREDGE_REMMEMBER_COOKIE} `; +
    `SolarEdge_Field_ID=${solaredgeID}`,

  const headers = {
    "Accept":            "application/json, text/plain, */*",
    "Accept-Language":   "en-GB,en;q=0.9,sl;q=0.8",
    "Referer":           "https://monitoring.solaredge.com/solaredge-web/p/site/3406940/",
    "User-Agent":        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With":  "XMLHttpRequest",
    "Cookie":            cookieString
  };
  
  try {
    const resp = await axios.get(solaredgeUrl, { headers });
    data = resp.data;
  } catch (e) {
    console.error("❌ Failed to fetch SolarEdge:", e.message);
    return;
  }

  const load    = parseFloat(data.load.currentPower);
  const pvPower = parseFloat(data.pv.currentPower);
  console.log(`Grid load=${load}W, PV power=${pvPower}W`);

  // 2) Compute stage
  let stage = 0;
  if (load > 7 && pvPower < 9) stage = 1;
  if (pvPower >= 9)                stage = 2;
  console.log(`→ desired stage=${stage}`);

  // 3) Connect to eWeLink
  const conn = new Ewelink({
    email:       process.env.EWELINK_EMAIL,
    password:    process.env.EWELINK_PASSWORD,
    region:      process.env.EWELINK_REGION,
    APP_ID:      process.env.EWELINK_APP_ID,
    APP_SECRET:  process.env.EWELINK_APP_SECRET
  });

  const devices  = await conn.getDevices();
  const deviceid = devices[0].deviceid;

  // Toggle helper
  async function ensure(channel, want) {
    const st = await conn.getDevicePowerState(deviceid, channel);
    if (st.state !== want) {
      console.log(`Channel${channel}: ${st.state} → toggling → ${want}`);
      await conn.setDevicePowerState(deviceid, "toggle", channel);
    } else {
      console.log(`Channel${channel} already ${want}`);
    }
  }

  // Stage→desired mapping:
  await ensure(1, stage === 2 ? "on"  : "off");
  await ensure(2, stage >= 1  ? "on"  : "off");
}

// Main loop: run forever, 1 min between
(async () => {
  console.log("🔄 Starting continuous loop (1 min interval) …");
  while (true) {
    try {
      await checkAndToggle();
    } catch (err) {
      console.error("🔥 Unexpected error:", err);
    }
    console.log("⏳ Sleeping 60 s …\n");
    await sleep(60_000);
  }
})();
