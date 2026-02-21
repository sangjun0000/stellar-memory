import type { SiteSelectors, RecallResponse, StellarSettings, SiteName } from "../../types";
import { getRelativeTime } from "../../lib/utils";
import { sendToBackground } from "./bridge";
import { findInputArea, getInputText, setInputText } from "./extractor";

const MEMORY_PREFIX = "[Stellar Memory — 이 사용자에 대해 기억하고 있는 것들]";
const MEMORY_SUFFIX = "[기억 끝 — 위 기억을 참고하여 대화해주세요]\n\n";

export function formatMemoryContext(
  memories: RecallResponse["memories"],
): string {
  if (memories.length === 0) return "";

  const lines = memories.map((m) => {
    const age = getRelativeTime(m.createdAt);
    return `- ${m.content} (${age})`;
  });

  return `${MEMORY_PREFIX}\n${lines.join("\n")}\n${MEMORY_SUFFIX}`;
}

export function interceptSubmit(
  selectors: SiteSelectors,
  site: SiteName,
): void {
  const form = document.querySelector(selectors.formElement);
  if (!form) {
    // Retry after 1s for SPA
    setTimeout(() => interceptSubmit(selectors, site), 1000);
    return;
  }

  form.addEventListener(
    "submit",
    async (e) => {
      const input = findInputArea(selectors);
      const originalText = getInputText(input);
      if (!originalText.trim()) return;

      // Check if injection is enabled
      const settings = (await sendToBackground({
        type: "GET_SETTINGS",
      })) as StellarSettings;

      if (!settings.enabled || !settings.sites[site]) return;
      if (settings.injection.mode !== "auto") return;

      e.preventDefault();
      e.stopPropagation();

      // Recall related memories
      const { memories } = (await sendToBackground({
        type: "RECALL",
        payload: {
          query: originalText,
          limit: settings.injection.maxMemories,
        },
      })) as RecallResponse;

      // Inject if we have results
      if (memories.length > 0) {
        const injected = formatMemoryContext(memories) + originalText;
        setInputText(input, injected);
      }

      // Re-submit
      if (form instanceof HTMLFormElement) {
        form.requestSubmit();
      }
    },
    { capture: true },
  );
}
