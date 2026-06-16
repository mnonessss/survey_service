import bridge from "@vkontakte/vk-bridge";

const vkBridge = (bridge as { default?: typeof bridge }).default ?? bridge;

async function copyWithVkBridge(text: string): Promise<boolean> {
  if (typeof vkBridge.send !== "function") return false;
  try {
    await vkBridge.send("VKWebAppCopyText", { text });
    return true;
  } catch {
    return false;
  }
}

function copyWithExecCommand(text: string): boolean {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.top = "0";
  textarea.style.left = "0";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(textarea);
  return ok;
}

export async function copyToClipboard(text: string): Promise<void> {
  if (await copyWithVkBridge(text)) return;

  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      /* пробуем fallback */
    }
  }

  if (!copyWithExecCommand(text)) {
    throw new Error("Не удалось скопировать в буфер обмена");
  }
}
