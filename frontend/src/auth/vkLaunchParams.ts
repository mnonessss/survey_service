export type VkSilentAuthPayload = Record<string, string | number>;

const VK_PARAM_PREFIX = "vk_";

function parseNumeric(value: string): string | number {
  if (/^-?\d+$/.test(value)) {
    return parseInt(value, 10);
  }
  return value;
}

/** Параметры запуска VK Mini App из hash (#) или query (?). */
export function parseVkLaunchParams(): VkSilentAuthPayload | null {
  const raw = window.location.hash.substring(1) || window.location.search.substring(1);
  if (!raw) return null;

  const urlParams = new URLSearchParams(raw);
  const sign = urlParams.get("sign");
  const vkUserId = urlParams.get("vk_user_id");
  if (!sign || !vkUserId) return null;

  const requestData: VkSilentAuthPayload = {
    vk_user_id: parseInt(vkUserId, 10),
    sign,
  };

  for (const [key, value] of urlParams.entries()) {
    if (key === "sign" || key === "vk_user_id") continue;
    if (key.startsWith(VK_PARAM_PREFIX)) {
      requestData[key] = parseNumeric(value);
    }
  }

  return requestData;
}
