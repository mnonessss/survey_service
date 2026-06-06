import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, getAccessToken, initCsrf } from "../api/client";
import { questionTypeLabel } from "../utils/questionHints";

type SortBy = "completed_at" | "started_at" | "session_id";
type SortOrder = "asc" | "desc";

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("ru-RU");
}

function AnswerCell({ value, questionType }: { value: string; questionType: string }) {
  const isImage =
    (questionType === "IMAGE_UPLOAD" || questionType === "IMAGE_CHOICE") &&
    value.startsWith("/uploads/");
  if (isImage) {
    return <img src={value} alt="Ответ" className="response-thumb" />;
  }
  return <span>{value}</span>;
}

export default function SurveyResponses() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("completed_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [filterQuestionId, setFilterQuestionId] = useState("");

  const load = useCallback(async () => {
    if (!id) return;
    const res = await api.getSurveyResponses(id, { sortBy, sortOrder });
    setData(res);
  }, [id, sortBy, sortOrder]);

  useEffect(() => {
    initCsrf()
      .then(load)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [load]);

  const rows = useMemo(() => {
    if (!data?.rows) return [];
    return data.rows;
  }, [data]);

  const exportXls = () => {
    if (!id) return;
    const res = fetch(api.exportUrl(id), {
      headers: { Authorization: `Bearer ${getAccessToken()}` },
      credentials: "include",
    });
    res.then(async (r) => {
      if (!r.ok) throw new Error("Export failed");
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `survey_${id}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    });
  };

  if (error && !data) return <div className="card error">{error}</div>;
  if (!data) return <p>Загрузка...</p>;

  return (
    <>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
          <div>
            <h2>Ответы: {data.survey_title}</h2>
            <p style={{ color: "#555", margin: 0 }}>Всего завершённых прохождений: {data.total}</p>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Link to={`/surveys/${id}`} className="button-link secondary">
              ← Редактор
            </Link>
            <button className="secondary" onClick={exportXls}>
              Скачать XLS
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Фильтры и сортировка</h3>
        <div className="responses-toolbar">
          <div className="field" style={{ marginBottom: 0, minWidth: 200 }}>
            <label>Сортировать по</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortBy)}>
              <option value="completed_at">Дате завершения</option>
              <option value="started_at">Дате начала</option>
              <option value="session_id">ID сессии</option>
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0, minWidth: 160 }}>
            <label>Порядок</label>
            <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as SortOrder)}>
              <option value="desc">Сначала новые</option>
              <option value="asc">Сначала старые</option>
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0, minWidth: 220 }}>
            <label>Подсветить вопрос</label>
            <select value={filterQuestionId} onChange={(e) => setFilterQuestionId(e.target.value)}>
              <option value="">Все вопросы</option>
              {data.questions.map((q: any) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="card">
          <p style={{ margin: 0, color: "#666" }}>Пока нет завершённых ответов.</p>
        </div>
      ) : (
        <div className="card responses-table-wrap">
          <table className="responses-table">
            <thead>
              <tr>
                <th>Завершено</th>
                <th>Начато</th>
                <th>Сессия</th>
                {data.questions.map((q: any) => (
                  <th
                    key={q.id}
                    className={filterQuestionId === q.id ? "highlight-col" : undefined}
                    title={questionTypeLabel(q.question_type)}
                  >
                    {q.title}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row: any) => (
                <tr key={row.session_id}>
                  <td>{formatDate(row.completed_at)}</td>
                  <td>{formatDate(row.started_at)}</td>
                  <td className="mono">{String(row.session_id).slice(0, 8)}…</td>
                  {data.questions.map((q: any) => {
                    const answer = row.answers.find((a: any) => a.question_id === q.id);
                    const value = answer?.display_value ?? "—";
                    return (
                      <td
                        key={q.id}
                        className={filterQuestionId === q.id ? "highlight-col" : undefined}
                      >
                        <AnswerCell value={value} questionType={q.question_type} />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
