import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { questionHint } from "../utils/questionHints";

function escapeHtml(text: string) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

const TEXT_ANSWER_TYPES = ["TEXT", "RATING", "DATE", "IMAGE_UPLOAD"];

function buildAnswerPayload(
  questions: any[],
  answers: Record<string, string>,
  multiAnswers: Record<string, string[]>,
) {
  return questions.map((q: any) => ({
    question_id: q.id,
    value_text: TEXT_ANSWER_TYPES.includes(q.question_type) ? answers[q.id] || null : null,
    value_json: q.question_type.includes("CHOICE")
      ? q.question_type === "MULTIPLE_CHOICE"
        ? multiAnswers[q.id] || []
        : [answers[q.id]].filter(Boolean)
      : null,
  }));
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

  useEffect(() => {
    if (!token) return;
    api
      .publicSurvey(token)
      .then(setSurvey)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [token]);

  const start = async () => {
    if (!token || !survey) return;
    setError("");
    try {
      const res = await api.startSession(token);
      setSessionId(res.session_id);
      setSessionToken(res.session_token);
      try {
        const draft = await api.getDraft(res.session_id, res.session_token);
        if (draft?.answers && typeof draft.answers === "object" && !Array.isArray(draft.answers)) {
          const nextAnswers: Record<string, string> = {};
          const nextMulti: Record<string, string[]> = {};
          for (const q of survey.questions) {
            const item = draft.answers[q.id];
            if (!item) continue;
            if (q.question_type === "MULTIPLE_CHOICE" && Array.isArray(item.value_json)) {
              nextMulti[q.id] = item.value_json;
            } else if (item.value_text) {
              nextAnswers[q.id] = item.value_text;
            } else if (Array.isArray(item.value_json) && item.value_json.length) {
              nextAnswers[q.id] = String(item.value_json[0]);
            }
          }
          setAnswers(nextAnswers);
          setMultiAnswers(nextMulti);
        }
      } catch {
        /* no saved draft */
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const attachAnswerImage = async (questionId: string, file: File) => {
    if (!sessionId || !sessionToken) return;
    setError("");
    setUploading((prev) => ({ ...prev, [questionId]: true }));
    try {
      const { url } = await api.uploadAnswerImage(sessionId, sessionToken, questionId, file);
      setAnswers((prev) => ({ ...prev, [questionId]: url }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading((prev) => ({ ...prev, [questionId]: false }));
    }
  };

  const saveDraft = async () => {
    if (!sessionId || !sessionToken || !survey) return;
    setError("");
    try {
      const payload = buildAnswerPayload(survey.questions, answers, multiAnswers);
      await api.saveDraft(sessionId, sessionToken, payload);
      alert("Черновик сохранён");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const submit = async () => {
    if (!sessionId || !sessionToken || !survey || submitting) return;
    setError("");
    setSubmitting(true);
    try {
      const payload = buildAnswerPayload(survey.questions, answers, multiAnswers);
      await api.submitSurvey(sessionId, sessionToken, payload);
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  if (error && !survey) return <div className="container card error">{error}</div>;
  if (!survey) return <div className="container">Загрузка...</div>;
  if (done) return <div className="container card">Спасибо! Ответы сохранены.</div>;

  return (
    <div className="container">
      <div className="card">
        <h2>{escapeHtml(survey.title)}</h2>
        {!sessionId ? (
          <button onClick={start}>Начать опрос</button>
        ) : (
          <>
            {survey.questions.map((q: any) => (
              <div className="field" key={q.id}>
                <label>{escapeHtml(q.title)}</label>
                {questionHint(q.question_type) && (
                  <p className="field-hint">{questionHint(q.question_type)}</p>
                )}
                {q.question_type === "TEXT" ? (
                  <textarea
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                    placeholder="Ваш ответ"
                  />
                ) : q.question_type === "MULTIPLE_CHOICE" ? (
                  <div>
                    {q.options?.map((o: any) => (
                      <label key={o.id} className="choice-option">
                        <input
                          type="checkbox"
                          checked={(multiAnswers[q.id] || []).includes(o.value)}
                          onChange={(e) => {
                            const current = multiAnswers[q.id] || [];
                            const next = e.target.checked
                              ? [...current, o.value]
                              : current.filter((v) => v !== o.value);
                            setMultiAnswers({ ...multiAnswers, [q.id]: next });
                          }}
                        />
                        <span>{escapeHtml(o.label)}</span>
                      </label>
                    ))}
                  </div>
                ) : q.question_type === "IMAGE_CHOICE" ? (
                  <div className="image-choice-grid">
                    {q.options?.map((o: any) => (
                      <label key={o.id} className="image-choice-item">
                        <input
                          type="radio"
                          name={q.id}
                          checked={answers[q.id] === o.value}
                          onChange={() => setAnswers({ ...answers, [q.id]: o.value })}
                        />
                        <img src={o.image_url} alt={o.label} />
                        <span>{escapeHtml(o.label)}</span>
                      </label>
                    ))}
                  </div>
                ) : q.question_type === "IMAGE_UPLOAD" ? (
                  <>
                    <label className="file-input-label">
                      {uploading[q.id] ? "Загрузка..." : "Прикрепить картинку"}
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/gif,image/webp"
                        disabled={uploading[q.id]}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) attachAnswerImage(q.id, file);
                          e.target.value = "";
                        }}
                      />
                    </label>
                    {answers[q.id] && (
                      <img src={answers[q.id]} alt="Прикреплённое изображение" className="answer-image-preview" />
                    )}
                  </>
                ) : q.question_type === "DATE" ? (
                  <input
                    type="date"
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                  />
                ) : q.question_type === "RATING" ? (
                  <input
                    type="number"
                    min={1}
                    max={10}
                    step={1}
                    placeholder="От 1 до 10"
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                  />
                ) : q.question_type === "SINGLE_CHOICE" ? (
                  <select
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                  >
                    <option value="">— Выберите вариант —</option>
                    {q.options?.map((o: any) => (
                      <option key={o.id} value={o.value}>
                        {escapeHtml(o.label)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                  />
                )}
              </div>
            ))}
            {error && <p className="error">{error}</p>}
            <button className="secondary" onClick={saveDraft}>
              Сохранить черновик
            </button>{" "}
            <button onClick={submit} disabled={submitting}>
              {submitting ? "Отправка..." : "Отправить"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
