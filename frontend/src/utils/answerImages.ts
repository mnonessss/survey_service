const RESPONSE_UPLOAD_PREFIX = "/uploads/responses/";

function parseResponseUploadPath(
  storagePath: string,
): { sessionId: string; questionId: string; filename: string } | null {
  if (!storagePath.startsWith(RESPONSE_UPLOAD_PREFIX)) return null;
  const rest = storagePath.slice(RESPONSE_UPLOAD_PREFIX.length);
  const [sessionId, questionId, filename] = rest.split("/");
  if (!sessionId || !questionId || !filename) return null;
  return { sessionId, questionId, filename };
}

export function toOwnerResponseMediaUrl(surveyId: string, storagePath: string): string {
  const parsed = parseResponseUploadPath(storagePath);
  if (!parsed) return storagePath;
  const { sessionId, questionId, filename } = parsed;
  return `/surveys/${surveyId}/response-media/${sessionId}/${questionId}/${encodeURIComponent(filename)}`;
}

export function toSessionResponseMediaUrl(
  sessionId: string,
  sessionToken: string,
  storagePath: string,
): string {
  const parsed = parseResponseUploadPath(storagePath);
  if (!parsed) return storagePath;
  const { questionId, filename } = parsed;
  const params = new URLSearchParams({ st: sessionToken });
  return `/public/sessions/${sessionId}/media/${questionId}/${encodeURIComponent(filename)}?${params}`;
}

export function getAnswerImageUrls(
  answer: { value_text?: string | null; value_json?: unknown; display_value?: string } | undefined,
  questionType: string,
  options?: { surveyId?: string; sessionId?: string; sessionToken?: string },
): string[] {
  if (!answer) return [];

  const mapUrl = (url: string) => {
    if (!url.startsWith(RESPONSE_UPLOAD_PREFIX)) return url;
    if (options?.surveyId) return toOwnerResponseMediaUrl(options.surveyId, url);
    if (options?.sessionId && options?.sessionToken) {
      return toSessionResponseMediaUrl(options.sessionId, options.sessionToken, url);
    }
    return url;
  };

  if (questionType === "IMAGE_UPLOAD") {
    const url = answer.value_text ?? "";
    return url.startsWith("/uploads/") ? [mapUrl(url)] : [];
  }

  if (questionType === "IMAGE_UPLOAD_MULTIPLE") {
    if (!Array.isArray(answer.value_json)) return [];
    return answer.value_json
      .filter((url): url is string => typeof url === "string" && url.startsWith("/uploads/"))
      .map(mapUrl);
  }

  const display = answer.display_value ?? "";
  if (
    questionType === "IMAGE_CHOICE" &&
    typeof display === "string" &&
    display.startsWith("/uploads/")
  ) {
    return [mapUrl(display)];
  }

  return [];
}
