import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Icon24DeleteOutline, Icon24ViewOutline } from "@vkontakte/icons";
import {
  Button,
  Checkbox,
  CustomSelect,
  FormItem,
  Group,
  Input,
  ModalCard,
  Panel,
  PanelHeader,
  Placeholder,
  Slider,
  Spacing,
  Spinner,
  Textarea,
  Title,
} from "@vkontakte/vkui";
import { api } from "../api/client";
import { questionHint } from "../utils/questionHints";

const TEXT_ANSWER_TYPES = ["TEXT", "RATING", "DATE"];
const DRAFT_SAVE_DELAY_MS = 600;

function sessionStorageKey(linkToken: string) {
  return `survey_session:${linkToken}`;
}

function loadStoredSession(linkToken: string) {
  try {
    const raw = localStorage.getItem(sessionStorageKey(linkToken));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { sessionId?: string; sessionToken?: string };
    if (parsed.sessionId && parsed.sessionToken) {
      return { sessionId: parsed.sessionId, sessionToken: parsed.sessionToken };
    }
  } catch {
    /* ignore */
  }
  return null;
}

function storeSession(linkToken: string, sessionId: string, sessionToken: string) {
  localStorage.setItem(sessionStorageKey(linkToken), JSON.stringify({ sessionId, sessionToken }));
}

function clearStoredSession(linkToken: string) {
  localStorage.removeItem(sessionStorageKey(linkToken));
}

function buildAnswerPayload(
  questions: any[],
  answers: Record<string, string>,
  multiAnswers: Record<string, string[]>,
) {
  return questions.map((q: any) => {
    if (q.question_type === "IMAGE_UPLOAD") {
      return { question_id: q.id, value_text: answers[q.id] || null, value_json: null };
    }
    if (q.question_type === "IMAGE_UPLOAD_MULTIPLE") {
      return { question_id: q.id, value_text: null, value_json: multiAnswers[q.id] || [] };
    }
    return {
      question_id: q.id,
      value_text: TEXT_ANSWER_TYPES.includes(q.question_type) ? answers[q.id] || null : null,
      value_json: q.question_type.includes("CHOICE")
        ? q.question_type === "MULTIPLE_CHOICE"
          ? multiAnswers[q.id] || []
          : [answers[q.id]].filter(Boolean)
        : null,
    };
  });
}

export default function PublicSurvey() {
  const { token } = useParams<{ token: string }>();
  const [survey, setSurvey] = useState<any>(null);
  const [sessionId, setSessionId] = useState("");
  const [sessionToken, setSessionToken] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [multiAnswers, setMultiAnswers] = useState<Record<string, string[]>>({});
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState<Record<string, boolean>>({});
  const [resuming, setResuming] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const resumeAttempted = useRef(false);

  useEffect(() => {
    if (!token) return;
    api
      .publicSurvey(token)
      .then(setSurvey)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [token]);

  const applyDraftAnswers = (draft: { answers?: unknown }) => {
    if (!survey?.questions) return;
    if (!draft?.answers || typeof draft.answers !== "object" || Array.isArray(draft.answers)) return;

    const nextAnswers: Record<string, string> = {};
    const nextMulti: Record<string, string[]> = {};
    for (const q of survey.questions) {
      const item = (draft.answers as Record<string, { value_text?: string; value_json?: unknown }>)[q.id];
      if (!item) continue;
      if (
        (q.question_type === "MULTIPLE_CHOICE" || q.question_type === "IMAGE_UPLOAD_MULTIPLE") &&
        Array.isArray(item.value_json)
      ) {
        nextMulti[q.id] = item.value_json as string[];
      } else if (item.value_text) {
        nextAnswers[q.id] = item.value_text;
      } else if (Array.isArray(item.value_json) && item.value_json.length) {
        nextAnswers[q.id] = String(item.value_json[0]);
      }
    }
    setAnswers(nextAnswers);
    setMultiAnswers(nextMulti);
  };

  const beginSession = async (sid: string, stoken: string, persist: boolean) => {
    if (!token) return;
    setSessionId(sid);
    setSessionToken(stoken);
    if (persist) storeSession(token, sid, stoken);
    const draft = await api.getDraft(sid, stoken);
    applyDraftAnswers(draft);
  };

  const start = async () => {
    if (!token || !survey) return;
    setError("");
    try {
      const res = await api.startSession(token);
      await beginSession(res.session_id, res.session_token, true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    if (!token || !survey || sessionId || resumeAttempted.current) return;
    const stored = loadStoredSession(token);
    if (!stored) return;

    resumeAttempted.current = true;
    setResuming(true);
    beginSession(stored.sessionId, stored.sessionToken, false)
      .catch(() => {
        clearStoredSession(token);
        setSessionId("");
        setSessionToken("");
      })
      .finally(() => setResuming(false));
  }, [token, survey, sessionId]);

  useEffect(() => {
    if (!sessionId || !sessionToken || !survey || done) return;

    const timer = window.setTimeout(() => {
      const payload = buildAnswerPayload(survey.questions, answers, multiAnswers);
      api.saveDraft(sessionId, sessionToken, payload).catch(() => {
        /* автосохранение не мешает заполнению */
      });
    }, DRAFT_SAVE_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [sessionId, sessionToken, survey, answers, multiAnswers, done]);

  const attachAnswerImage = async (questionId: string, file: File, multiple: boolean) => {
    if (!sessionId || !sessionToken) return;
    setError("");
    setUploading((prev) => ({ ...prev, [questionId]: true }));
    try {
      const { url } = await api.uploadAnswerImage(sessionId, sessionToken, questionId, file);
      if (multiple) {
        setMultiAnswers((prev) => ({
          ...prev,
          [questionId]: [...(prev[questionId] || []), url],
        }));
      } else {
        setAnswers((prev) => ({ ...prev, [questionId]: url }));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading((prev) => ({ ...prev, [questionId]: false }));
    }
  };

  const removeUploadedImage = (questionId: string, url: string, multiple: boolean) => {
    if (multiple) {
      setMultiAnswers((prev) => ({
        ...prev,
        [questionId]: (prev[questionId] || []).filter((item) => item !== url),
      }));
    } else {
      setAnswers((prev) => {
        const next = { ...prev };
        delete next[questionId];
        return next;
      });
    }
  };

  const renderUploadedPreview = (url: string, questionId: string, multiple: boolean) => (
    <div key={url} className="vk-upload-preview-item">
      <button
        type="button"
        className="vk-response-thumb-btn"
        onClick={() => setLightboxSrc(url)}
        aria-label="Увеличить изображение"
      >
        <img src={url} alt="Ответ" className="vk-answer-preview" />
      </button>
      <button
        type="button"
        className="vk-upload-remove-btn"
        aria-label="Удалить изображение"
        onClick={() => removeUploadedImage(questionId, url, multiple)}
      >
        <Icon24DeleteOutline />
      </button>
    </div>
  );

  const submit = async () => {
    if (!sessionId || !sessionToken || !survey || submitting) return;
    setError("");
    setSubmitting(true);
    try {
      const payload = buildAnswerPayload(survey.questions, answers, multiAnswers);
      await api.submitSurvey(sessionId, sessionToken, payload);
      if (token) clearStoredSession(token);
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  if (error && !survey) {
    return (
      <Panel id="public">
        <PanelHeader>Опрос</PanelHeader>
        <Placeholder title="Ошибка">{error}</Placeholder>
      </Panel>
    );
  }

  if (!survey) {
    return (
      <Panel id="public">
        <PanelHeader>Опрос</PanelHeader>
        <Placeholder>
          <Spinner size="l" />
        </Placeholder>
      </Panel>
    );
  }

  if (done) {
    return (
      <Panel id="public">
        <PanelHeader>Опрос</PanelHeader>
        <Placeholder title="Спасибо!">Ответы сохранены.</Placeholder>
      </Panel>
    );
  }

  return (
    <Panel id="public">
      <ModalCard
        id="public-image-lightbox"
        className="vk-lightbox-modal"
        size={1200}
        open={!!lightboxSrc}
        onClose={() => setLightboxSrc(null)}
        dismissButtonMode="inside"
        dismissLabel="Закрыть"
      >
        {lightboxSrc && (
          <div className="vk-lightbox-viewport">
            <img src={lightboxSrc} alt="Увеличенное изображение" className="vk-lightbox-img" />
          </div>
        )}
      </ModalCard>

      <PanelHeader>{survey.title}</PanelHeader>
      {survey.description && (
        <Group>
          <Title level="3" weight="3" style={{ padding: "0 16px" }}>
            {survey.description}
          </Title>
        </Group>
      )}

      {resuming ? (
        <Group>
          <Placeholder>
            <Spinner size="l" />
            Загрузка ответов...
          </Placeholder>
        </Group>
      ) : !sessionId ? (
        <Group>
          <FormItem>
            <Button size="l" stretched onClick={start}>
              Начать опрос
            </Button>
          </FormItem>
        </Group>
      ) : (
        <>
          {survey.questions.map((q: any) => (
            <Group key={q.id}>
              {questionHint(q.question_type) && (
                <FormItem>
                  <p className="vk-question-hint">{questionHint(q.question_type)}</p>
                </FormItem>
              )}
              <FormItem>
                <p className="vk-question-title">
                  {q.title}
                  {q.required ? " *" : ""}
                </p>
              </FormItem>

              {q.question_type === "TEXT" && (
                <FormItem>
                  <Textarea
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                    placeholder="Ваш ответ"
                  />
                </FormItem>
              )}

              {q.question_type === "MULTIPLE_CHOICE" &&
                q.options?.map((o: any) => (
                  <Checkbox
                    key={o.id}
                    checked={(multiAnswers[q.id] || []).includes(o.value)}
                    onChange={(e) => {
                      const current = multiAnswers[q.id] || [];
                      const next = e.target.checked
                        ? [...current, o.value]
                        : current.filter((v) => v !== o.value);
                      setMultiAnswers({ ...multiAnswers, [q.id]: next });
                    }}
                  >
                    {o.label}
                  </Checkbox>
                ))}

              {q.question_type === "SINGLE_CHOICE" && (
                <FormItem>
                  <CustomSelect
                    placeholder="Выберите вариант"
                    value={answers[q.id] || null}
                    onChange={(_, v) => setAnswers({ ...answers, [q.id]: String(v ?? "") })}
                    options={q.options?.map((o: any) => ({ label: o.label, value: o.value })) ?? []}
                  />
                </FormItem>
              )}

              {q.question_type === "IMAGE_CHOICE" && (
                <FormItem>
                  <div className="vk-image-choice-grid">
                    {q.options?.map((o: any) => (
                      <div key={o.id} className="vk-image-choice-item">
                        <div className="vk-image-choice-frame">
                          <button
                            type="button"
                            className={
                              answers[q.id] === o.value
                                ? "vk-image-choice-btn vk-image-choice-btn--selected"
                                : "vk-image-choice-btn"
                            }
                            onClick={() => setAnswers({ ...answers, [q.id]: o.value })}
                            aria-label="Выбрать вариант"
                            aria-pressed={answers[q.id] === o.value}
                          >
                            <img src={o.image_url} alt="" />
                          </button>
                          <button
                            type="button"
                            className="vk-image-choice-zoom"
                            aria-label="Увеличить изображение"
                            onClick={() => setLightboxSrc(o.image_url)}
                          >
                            <Icon24ViewOutline />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </FormItem>
              )}

              {q.question_type === "IMAGE_UPLOAD" && (
                <FormItem>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    hidden
                    ref={(el) => {
                      fileRefs.current[q.id] = el;
                    }}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) attachAnswerImage(q.id, file, false);
                      e.target.value = "";
                    }}
                  />
                  <Button
                    mode="secondary"
                    stretched
                    loading={uploading[q.id]}
                    onClick={() => fileRefs.current[q.id]?.click()}
                  >
                    Прикрепить картинку
                  </Button>
                  {answers[q.id] && renderUploadedPreview(answers[q.id], q.id, false)}
                </FormItem>
              )}

              {q.question_type === "IMAGE_UPLOAD_MULTIPLE" && (
                <FormItem>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    hidden
                    ref={(el) => {
                      fileRefs.current[q.id] = el;
                    }}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) attachAnswerImage(q.id, file, true);
                      e.target.value = "";
                    }}
                  />
                  <Button
                    mode="secondary"
                    stretched
                    loading={uploading[q.id]}
                    onClick={() => fileRefs.current[q.id]?.click()}
                  >
                    Добавить картинку
                  </Button>
                  {(multiAnswers[q.id] || []).length > 0 && (
                    <div className="vk-upload-preview-grid">
                      {(multiAnswers[q.id] || []).map((url) =>
                        renderUploadedPreview(url, q.id, true),
                      )}
                    </div>
                  )}
                </FormItem>
              )}

              {q.question_type === "DATE" && (
                <FormItem>
                  <Input
                    type="date"
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                  />
                </FormItem>
              )}

              {q.question_type === "RATING" && (
                <FormItem>
                  <div className="vk-rating-slider">
                    <Title level="2" weight="2" className="vk-rating-value">
                      {answers[q.id] ? `${answers[q.id]} из 10` : "Выберите оценку от 1 до 10"}
                    </Title>
                    <Slider
                      min={1}
                      max={10}
                      step={1}
                      value={answers[q.id] ? Number(answers[q.id]) : 1}
                      onChange={(value) => setAnswers({ ...answers, [q.id]: String(value) })}
                      withTooltip
                    />
                    <div className="vk-rating-scale">
                      <span>1 — низкая</span>
                      <span>10 — высокая</span>
                    </div>
                  </div>
                </FormItem>
              )}
            </Group>
          ))}

          {error && (
            <Group>
              <FormItem>
                <Title level="3" style={{ color: "var(--vkui--color_text_negative)" }}>
                  {error}
                </Title>
              </FormItem>
            </Group>
          )}

          <Spacing size={8} />
          <Group>
            <FormItem>
              <Button size="l" stretched onClick={submit} loading={submitting}>
                Отправить
              </Button>
            </FormItem>
          </Group>
        </>
      )}
    </Panel>
  );
}
