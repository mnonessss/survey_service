import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Button,
  CustomSelect,
  FormItem,
  Group,
  Header,
  HorizontalScroll,
  ModalCard,
  Placeholder,
  Spinner,
  Title,
} from "@vkontakte/vkui";
import { api, getAccessToken, initCsrf } from "../api/client";
import { getAnswerImageUrls } from "../utils/answerImages";
import { questionTypeLabel } from "../utils/questionHints";

type SortBy = "completed_at" | "started_at";
type SortOrder = "asc" | "desc";

const SORT_BY_OPTIONS = [
  { label: "Дате завершения", value: "completed_at" },
  { label: "Дате начала", value: "started_at" },
];

const SORT_ORDER_OPTIONS = [
  { label: "Сначала новые", value: "desc" },
  { label: "Сначала старые", value: "asc" },
];

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("ru-RU");
}

export default function SurveyResponses() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("completed_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);

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

  const rows = useMemo(() => data?.rows ?? [], [data]);

  const exportXls = () => {
    if (!id) return;
    fetch(api.exportUrl(id), {
      headers: { Authorization: `Bearer ${getAccessToken()}` },
      credentials: "include",
    }).then(async (r) => {
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

  if (error && !data) {
    return <Placeholder title="Ошибка">{error}</Placeholder>;
  }

  if (!data) {
    return (
      <Placeholder>
        <Spinner size="l" />
      </Placeholder>
    );
  }

  return (
    <>
      <ModalCard
        id="image-lightbox"
        className="vk-lightbox-modal"
        size={1200}
        open={!!lightboxSrc}
        onClose={() => setLightboxSrc(null)}
        dismissButtonMode="inside"
        dismissLabel="Закрыть"
      >
        {lightboxSrc && (
          <div className="vk-lightbox-viewport">
            <img src={lightboxSrc} alt="Ответ" className="vk-lightbox-img" />
          </div>
        )}
      </ModalCard>

      <Group
        header={<Header size="s">Ответы: {data.survey_title}</Header>}
        description={`Всего завершённых прохождений: ${data.total}`}
      >
        <FormItem>
          <Button mode="secondary" size="m" onClick={() => navigate(`/surveys/${id}`)}>
            ← Редактор
          </Button>
          {" "}
          <Button mode="secondary" size="m" onClick={exportXls}>
            Скачать XLS
          </Button>
        </FormItem>
      </Group>

      <Group header={<Header size="s">Сортировка</Header>}>
        <FormItem top="Сортировать по">
          <CustomSelect
            value={sortBy}
            onChange={(_, v) => setSortBy((v as SortBy) ?? "completed_at")}
            options={SORT_BY_OPTIONS}
          />
        </FormItem>
        <FormItem top="Порядок">
          <CustomSelect
            value={sortOrder}
            onChange={(_, v) => setSortOrder((v as SortOrder) ?? "desc")}
            options={SORT_ORDER_OPTIONS}
          />
        </FormItem>
      </Group>

      {rows.length === 0 ? (
        <Placeholder>Пока нет завершённых ответов.</Placeholder>
      ) : (
        <Group header={<Header size="s">Таблица ответов</Header>}>
          <HorizontalScroll>
            <table className="vk-responses-table">
              <thead>
                <tr>
                  <th>Начато</th>
                  <th>Завершено</th>
                  {data.questions.map((q: any) => (
                    <th key={q.id} title={questionTypeLabel(q.question_type)}>
                      {q.title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row: any) => (
                  <tr key={row.session_id}>
                    <td>{formatDate(row.started_at)}</td>
                    <td>{formatDate(row.completed_at)}</td>
                    {data.questions.map((q: any) => {
                      const answer = row.answers.find((a: any) => a.question_id === q.id);
                      const imageUrls = getAnswerImageUrls(answer, q.question_type);
                      const value = answer?.display_value ?? "—";
                      return (
                        <td key={q.id}>
                          {imageUrls.length > 0 ? (
                            <div className="vk-response-images">
                              {imageUrls.map((url) => (
                                <button
                                  key={url}
                                  type="button"
                                  className="vk-response-thumb-btn"
                                  onClick={() => setLightboxSrc(url)}
                                  aria-label="Увеличить изображение"
                                >
                                  <img src={url} alt="Ответ" className="vk-response-thumb" />
                                </button>
                              ))}
                            </div>
                          ) : (
                            value
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </HorizontalScroll>
        </Group>
      )}
    </>
  );
}
