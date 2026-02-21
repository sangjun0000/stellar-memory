import type { StellarSettings } from "../types";
import { DEFAULT_SETTINGS } from "../types";

const STORAGE_KEY = "stellar_settings";

export class SettingsManager {
  async getAll(): Promise<StellarSettings> {
    const result = await chrome.storage.local.get(STORAGE_KEY);
    return { ...DEFAULT_SETTINGS, ...result[STORAGE_KEY] };
  }

  async update(partial: Partial<StellarSettings>): Promise<StellarSettings> {
    const current = await this.getAll();
    const merged = deepMerge(current as unknown as Record<string, unknown>, partial as unknown as Record<string, unknown>) as unknown as StellarSettings;
    await chrome.storage.local.set({ [STORAGE_KEY]: merged as unknown as Record<string, unknown> });
    return merged;
  }

  async reset(): Promise<StellarSettings> {
    await chrome.storage.local.set({ [STORAGE_KEY]: DEFAULT_SETTINGS });
    return DEFAULT_SETTINGS;
  }

  onChange(callback: (settings: StellarSettings) => void): void {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === "local" && changes[STORAGE_KEY]) {
        callback(changes[STORAGE_KEY].newValue as StellarSettings);
      }
    });
  }
}

function deepMerge(target: Record<string, unknown>, source: Record<string, unknown>): Record<string, unknown> {
  const result = { ...target };
  for (const key of Object.keys(source)) {
    const sv = source[key];
    const tv = target[key];
    if (sv && typeof sv === "object" && !Array.isArray(sv) && tv && typeof tv === "object" && !Array.isArray(tv)) {
      result[key] = deepMerge(tv as Record<string, unknown>, sv as Record<string, unknown>);
    } else {
      result[key] = sv;
    }
  }
  return result;
}
