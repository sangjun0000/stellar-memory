interface Props {
  mode: "auto" | "manual";
  onChange: (mode: "auto" | "manual") => void;
}

export function InjectionMode({ mode, onChange }: Props) {
  return (
    <div className="px-4 py-2 border-t border-gray-100">
      <div className="text-xs font-semibold text-gray-500 mb-1">기억 주입</div>
      <div className="flex gap-3">
        <label className="flex items-center gap-1 text-sm cursor-pointer">
          <input
            type="radio"
            name="injection-mode"
            checked={mode === "auto"}
            onChange={() => onChange("auto")}
            className="accent-stellar-500"
          />
          자동
        </label>
        <label className="flex items-center gap-1 text-sm cursor-pointer">
          <input
            type="radio"
            name="injection-mode"
            checked={mode === "manual"}
            onChange={() => onChange("manual")}
            className="accent-stellar-500"
          />
          수동
        </label>
      </div>
    </div>
  );
}
