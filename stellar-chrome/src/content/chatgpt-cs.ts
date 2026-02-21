import { SELECTORS } from "./selectors";
import { createConversationObserver } from "./shared/observer";
import { interceptSubmit } from "./shared/injector";
import { sendToBackground, trackInputChanges } from "./shared/bridge";
import type { SiteName, StorePayload } from "../types";

const site: SiteName = "chatgpt";
const sel = SELECTORS[site];

// 1. Capture conversations
createConversationObserver(sel, async (msg) => {
  const payload: StorePayload = {
    content: `[${msg.role}] ${msg.content}`,
    importance: msg.role === "user" ? 0.6 : 0.4,
    metadata: {
      source: site,
      url: window.location.href,
      role: msg.role,
      timestamp: Date.now(),
    },
  };
  await sendToBackground({ type: "STORE", payload });
});

// 2. Inject memories on submit
interceptSubmit(sel, site);

// 3. Track input changes for Side Panel real-time recall
trackInputChanges(sel);
