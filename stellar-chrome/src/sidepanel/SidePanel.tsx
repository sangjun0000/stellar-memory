import React, { useEffect, useState, useCallback, useRef } from "react";
import { MemoryCard } from "./MemoryCard";
import type { MemoryRecord, StellarSettings } from "../types";

const DEBOUNCE_MS = 500;

export function SidePanel() {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [injectionEnabled, setInjectionEnabled] = useState(true);
  const [currentQuery, setCurrentQuery] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const loadRelatedMemories = useCallback((query: string) => {
    chrome.runtime.sendMessage(
      { type: "RECALL", payload: { query, limit: 10 } },
      (res) => {
        if (res?.memories) setMemories(res.memories);
      },
    );
  }, []);

  // Listen for real-time input updates from content scripts
  useEffect(() => {
    loadRelatedMemories("");

    // Listen for tab changes
    chrome.tabs?.onActivated?.addListener(() => loadRelatedMemories(""));

    // Listen for input text updates from content scripts (real-time tracking)
    const messageListener = (
      msg: { type: string; payload?: { text: string } },
      _sender: chrome.runtime.MessageSender,
      _sendResponse: (response?: unknown) => void,
    ) => {
      if (msg.type === "INPUT_CHANGED" && msg.payload?.text !== undefined) {
        const text = msg.payload.text;
        setCurrentQuery(text);

        // 500ms debounce before recall
        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
          loadRelatedMemories(text);
        }, DEBOUNCE_MS);
      }
    };

    chrome.runtime.onMessage.addListener(messageListener);
    return () => {
      chrome.runtime.onMessage.removeListener(messageListener);
      clearTimeout(debounceRef.current);
    };
  }, [loadRelatedMemories]);

  function toggleInjection() {
    const newMode = injectionEnabled ? "manual" : "auto";
    chrome.runtime.sendMessage(
      { type: "GET_SETTINGS" },
      (settings: StellarSettings) => {
        chrome.runtime.sendMessage(
          {
            type: "UPDATE_SETTINGS",
            payload: { injection: { ...settings.injection, mode: newMode } },
          },
          () => setInjectionEnabled(!injectionEnabled),
        );
      },
    );
  }

  return (
    <div className="flex flex-col h-full bg-white text-gray-900">
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="font-bold text-sm">&#128204; 이 대화와 관련된 기억</h2>
        {currentQuery && (
          <p className="text-xs text-gray-400 mt-1 truncate">
            검색: {currentQuery}
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2">
        {memories.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <p className="text-sm">관련 기억이 없습니다</p>
          </div>
        ) : (
          memories.map((m) => <MemoryCard key={m.id} memory={m} />)
        )}
      </div>

      <div className="px-4 py-3 border-t border-gray-200 text-center">
        <p className="text-xs text-gray-500 mb-1">
          &#128161;{" "}
          {injectionEnabled
            ? "기억이 자동 주입됩니다"
            : "자동 주입이 꺼져있습니다"}
        </p>
        <button
          onClick={toggleInjection}
          className="text-xs text-stellar-600 hover:text-stellar-700 font-medium"
        >
          {injectionEnabled ? "[주입 끄기]" : "[주입 켜기]"}
        </button>
      </div>
    </div>
  );
}
