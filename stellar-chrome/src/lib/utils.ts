export function getRelativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffDay > 30) return `${Math.floor(diffDay / 30)}달 전`;
  if (diffDay > 0) return `${diffDay}일 전`;
  if (diffHour > 0) return `${diffHour}시간 전`;
  if (diffMin > 0) return `${diffMin}분 전`;
  return "방금 전";
}

export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  ms: number,
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

export function zoneLabel(zone: number): string {
  switch (zone) {
    case 0: return "Core";
    case 1: return "Inner";
    case 2: return "Outer";
    case 3: return "Belt";
    default: return "Unknown";
  }
}

export function zoneEmoji(zone: number): string {
  switch (zone) {
    case 0: return "\u2600\uFE0F";  // sun
    case 1: return "\uD83E\uDE90";  // ringed planet
    case 2: return "\u2B50";        // star
    case 3: return "\uD83C\uDF0C";  // milky way
    default: return "\u2728";       // sparkles
  }
}
