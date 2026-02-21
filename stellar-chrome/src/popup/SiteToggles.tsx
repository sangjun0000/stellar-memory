import React from "react";

interface Props {
  sites: { chatgpt: boolean; claude: boolean; gemini: boolean };
  onToggle: (site: "chatgpt" | "claude" | "gemini") => void;
}

const SITE_LABELS: Record<string, string> = {
  chatgpt: "ChatGPT",
  claude: "Claude",
  gemini: "Gemini",
};

export function SiteToggles({ sites, onToggle }: Props) {
  return (
    <div className="px-4 py-2">
      <div className="text-xs font-semibold text-gray-500 mb-1">사이트 설정</div>
      <div className="flex flex-col gap-1">
        {(Object.keys(sites) as Array<"chatgpt" | "claude" | "gemini">).map(
          (site) => (
            <div
              key={site}
              className="flex items-center justify-between py-1"
            >
              <span className="text-sm text-gray-700">
                {SITE_LABELS[site]}
              </span>
              <button
                onClick={() => onToggle(site)}
                className={`relative w-10 h-5 rounded-full transition-colors ${
                  sites[site] ? "bg-stellar-500" : "bg-gray-300"
                }`}
              >
                <span
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                    sites[site] ? "translate-x-5" : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
          ),
        )}
      </div>
    </div>
  );
}
