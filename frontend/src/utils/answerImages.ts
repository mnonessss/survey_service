export function getAnswerImageUrls(
  answer: { value_text?: string | null; value_json?: unknown; display_value?: string } | undefined,
  questionType: string,
): string[] {
  if (!answer) return [];

  if (questionType === "IMAGE_UPLOAD") {
    const url = answer.value_text ?? "";
    return url.startsWith("/uploads/") ? [url] : [];
  }

  if (questionType === "IMAGE_UPLOAD_MULTIPLE") {
    if (!Array.isArray(answer.value_json)) return [];
    return answer.value_json.filter(
      (url): url is string => typeof url === "string" && url.startsWith("/uploads/"),
    );
  }

  const display = answer.display_value ?? "";
  if (
    questionType === "IMAGE_CHOICE" &&
    typeof display === "string" &&
    display.startsWith("/uploads/")
  ) {
    return [display];
  }

  return [];
}
