import axios from "axios";
import Ewelink from "ewelink-api";
import { config } from "dotenv";

config();

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchSolarEdge() {
  const {
    SOLAREDGE_URL,
    SOLAREDGE_REFERER,
    SOLAREDGE_COOKIEYES_CONSENT,
    SOLAREDGE_CSRF_TOKEN,
    SOLAREDGE_CLIENT,
    SOLAREDGE_LOCALE,
    SOLAREDGE_SSO,
    SOLAREDGE_REMMEMBER_COOKIE,
    SOLAREDGE_FIELD_ID
  } = process.env;

  const cookieString = [
    `cookieyes-consent=${SOLAREDGE_COOKIEYES_CONSENT}`,
    `CSRF-TOKEN=${SOLAREDGE_CSRF_TOKEN}`,
    `SolarEdge_Client-1.6=${SOLAREDGE_CLIENT}`,
    `SolarEdge_Locale=${SOLAREDGE_LOCALE}`,
    `SolarEdge_SSO-1.4=${SOLAREDGE_SSO}`,
    `SolarEdge_Locale=${SOLAREDGE_LOCALE}`,
    `SPRING_SECURITY_REMEMBER_ME_COOKIE=${SOLAREDGE_REMMEMBER_COOKIE}`,
    `SolarEdge_Field_ID=${SOLAREDGE_FIELD_ID}`
  ].join("; ");

  const headers = {
    "Accept":            "application/json, text/plain, */*",
    "Accept-Language":   "en-GB,en;q=0.9,sl;q=0.8",
    "Referer":           process.env.SOLAREDGE_REFERER,
    "User-Agent":        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " +
                         "AppleWebKit/537.36 (KHTML, like Gecko) " +
                         "Chrome/134.0.0.0 Safari/537.36",
    "X-Requested-With":  "XMLHttpRequest",
    "Cookie":            cookieString
  };

  try {
    const resp = await axios.get(SOLAREDGE_URL, { headers });

    if (!resp.data || typeof resp.data !== 'object') {
      throw new Error('Invalid or incomplete response data');
    }
    console.log("✅ Status:", resp.status);
    return resp.data;
  } catch (err) {
    console.error("❌ fetch failed:", err.response?.status);
    throw err;
  }
}


async function checkAndToggle(counters) {
  const now = new Date();
  const h = now.getUTCHours();

  // Only run between 11 ≤ UTC < 19
  if (h < 9 || h >= 17) {
    console.log(`Outside 9–17 UTC (hour=${h}) — sleeping only.`);
    return;
  }

  const data = await fetchSolarEdge();

  const load    = parseFloat(data.consumption.currentPower);
  const pvPower = parseFloat(data.solarProduction.currentPower);
  const gridExport = pvPower - load;
  console.log(`Load=${load}W, PV power=${pvPower}W -> Grid=${gridExport}`);
  await setHeaters(gridExport, counters);
}
  
async function setHeaters(gridExport, counters) {
  const conn = new Ewelink({
    email:       process.env.EWELINK_EMAIL,
    password:    process.env.EWELINK_PASSWORD,
    region:      process.env.EWELINK_REGION,
    APP_ID:      process.env.EWELINK_APP_ID,
    APP_SECRET:  process.env.EWELINK_APP_SECRET,
  });
  const devices = await conn.getDevices();
  const id      = devices[0].deviceid;

  const st1 = await conn.getDevicePowerState(id, 1);
  const st2 = await conn.getDevicePowerState(id, 2);
  const h1On = st1.state === "on";
  const h2On = st2.state === "on";

  const adjusted = gridExport + (h1On ? 2 : 0) + (h2On ? 4 : 0);

  let want1 = false, want2 = false;
  if (adjusted >= 9) {
    want1 = true; want2 = true;
  } else if (adjusted >= 7) {
    want1 = true; want2 = false;
  }

  async function ensure(ch, currentlyOn, wantOn) {
    if (currentlyOn !== wantOn) {
      console.log(`↔︎ Channel${ch}: ${currentlyOn ? "on" : "off"} → toggling → ${wantOn ? "on" : "off"}`);
      await conn.setDevicePowerState(id, "toggle", ch);
    }
  }

  await ensure(1, h1On, want1);
  await ensure(2, h2On, want2);

  // update counters
  const key = want1 && want2
    ? "both"
    : want1
      ? "ch1"
      : "off";
  counters[key] += 2;

  console.log(
    `⏱ adjusted=${adjusted.toFixed(2)} kW → state=${key}, ` +
    `totals: off=${counters.off} m, ch1=${counters.ch1} m, both=${counters.both} m`
  );
}


(async () => {
  console.log("🔄 Starting continuous loop (2 min interval) …");
  const counters = { off: 0, ch1: 0, both: 0 };

  while (true) {
    try {
      await checkAndToggle(counters);
    } catch (err) {
      console.error("🔥 Unexpected error:", err);
    }
    console.log("⏳ Sleeping 120 s …\n");
    await sleep(120_000);
  }
})();
