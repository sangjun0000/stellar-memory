import { ApiClient } from "../lib/api-client";
import { SettingsManager } from "../lib/settings-manager";
import type { CSMessage, StellarSettings } from "../types";

const api = new ApiClient();
const settings = new SettingsManager();

// ─── Message Router ───

chrome.runtime.onMessage.addListener(
  (msg: CSMessage, _sender, sendResponse) => {
    handleMessage(msg).then(sendResponse);
    return true; // keep channel open for async
  },
);

async function handleMessage(msg: CSMessage): Promise<unknown> {
  switch (msg.type) {
    case "STORE": {
      const result = await api.store(msg.payload);
      if (result.id) {
        const s = await settings.getAll();
        await settings.update({
          stats: { ...s.stats, totalStored: s.stats.totalStored + 1, lastSync: new Date().toISOString() },
        });
      }
      return result;
    }

    case "RECALL":
      return api.recall(msg.payload);

    case "FORGET":
      return api.forget(msg.payload.memoryId);

    case "GET_SETTINGS":
      return settings.getAll();

    case "UPDATE_SETTINGS":
      return settings.update(msg.payload);

    case "GET_STATS":
      return api.getStats();

    case "CHECK_CONNECTION":
      return { connected: await api.checkHealth() };

    default:
      return { error: "Unknown message type" };
  }
}

// ─── Periodic Health Check (30s) ───

async function healthCheck() {
  const connected = await api.checkHealth();
  const current = await settings.getAll();

  if (current.api.connected !== connected) {
    await settings.update({ api: { ...current.api, connected } });
  }

  // Flush offline queue when reconnected
  if (connected && !current.api.connected) {
    await api.flushQueue();
  }
}

setInterval(healthCheck, 30_000);

// ─── On Install ───

chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === "install") {
    await settings.reset();
    await healthCheck();
  }
});

// ─── Side Panel ───

chrome.sidePanel?.setPanelBehavior?.({ openPanelOnActionClick: false });
