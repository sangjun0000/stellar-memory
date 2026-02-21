import React from "react";

interface Props {
  query: string;
  onChange: (q: string) => void;
}

export function SearchBar({ query, onChange }: Props) {
  return (
    <div className="px-4 py-2 border-b border-gray-100">
      <input
        type="text"
        value={query}
        onChange={(e) => onChange(e.target.value)}
        placeholder="&#128269; 기억 검색..."
        className="w-full px-3 py-2 text-sm rounded-lg bg-gray-100 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-stellar-400"
      />
    </div>
  );
}
