import React, { useEffect, useState } from "react";
import { SearchBar } from "./SearchBar";
import { StatusBar } from "./StatusBar";
import { MemoryList } from "./MemoryList";
import { SiteToggles } from "./SiteToggles";
import { InjectionMode } from "./InjectionMode";
import type { StellarSettings, MemoryRecord, StatsResponse } from "../types";

export function Popup() {
  const [settings, setSettings] = useState<StellarSettings | null>(null);
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    chrome.runtime.sendMessage({ type: "GET_SETTINGS" }, (s) => setSettings(s));
    chrome.runtime.sendMessage({ type: "GET_STATS" }, (s) => setStats(s));
    // Load recent memories
    chrome.runtime.sendMessage(
      { type: "RECALL", payload: { query: "", limit: 20 } },
      (res) => {
        if (res?.memories) setMemories(res.memories);
      },
    );
  }, []);

  useEffect(() => {
    if (!searchQuery) return;
    const timer = setTimeout(() => {
      chrome.runtime.sendMessage(
        { type: "RECALL", payload: { query: searchQuery, limit: 20 } },
        (res) => {
          if (res?.memories) setMemories(res.memories);
        },
      );
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  function handleToggleEnabled() {
    if (!settings) return;
    const updated = { enabled: !settings.enabled };
    chrome.runtime.sendMessage(
      { type: "UPDATE_SETTINGS", payload: updated },
      (s) => setSettings(s),
    );
  }

  function handleSiteToggle(site: "chatgpt" | "claude" | "gemini") {
    if (!settings) return;
    const updated = {
      sites: { ...settings.sites, [site]: !settings.sites[site] },
    };
    chrome.runtime.sendMessage(
      { type: "UPDATE_SETTINGS", payload: updated },
      (s) => setSettings(s),
    );
  }

  function handleModeChange(mode: "auto" | "manual") {
    if (!settings) return;
    const updated = { injection: { ...settings.injection, mode } };
    chrome.runtime.sendMessage(
      { type: "UPDATE_SETTINGS", payload: updated },
      (s) => setSettings(s),
    );
  }

  function handleDelete(memoryId: string) {
    chrome.runtime.sendMessage(
      { type: "FORGET", payload: { memoryId } },
      () => {
        setMemories((prev) => prev.filter((m) => m.id !== memoryId));
      },
    );
  }

  if (!settings) {
    return (
      <div className="p-4 text-center text-gray-500">Loading...</div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white text-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <span className="text-xl">&#9728;&#65039;</span>
          <span className="font-bold text-lg">Stellar Memory</span>
        </div>
        <button
          onClick={handleToggleEnabled}
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            settings.enabled
              ? "bg-stellar-500 text-white"
              : "bg-gray-200 text-gray-600"
          }`}
        >
          {settings.enabled ? "ON" : "OFF"}
        </button>
      </div>

      <SearchBar query={searchQuery} onChange={setSearchQuery} />

      <StatusBar
        connected={settings.api.connected}
        totalMemories={stats?.total_memories ?? settings.stats.totalStored}
      />

      <div className="flex-1 overflow-y-auto">
        <MemoryList memories={memories} onDelete={handleDelete} />
      </div>

      <div className="border-t border-gray-200">
        <SiteToggles sites={settings.sites} onToggle={handleSiteToggle} />
        <InjectionMode
          mode={settings.injection.mode}
          onChange={handleModeChange}
        />
      </div>
    </div>
  );
}
