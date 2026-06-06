import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, getAccessToken, initCsrf } from "../api/client";
import { questionHint, questionTypeLabel } from "../utils/questionHints";

const TEXT_CHOICE_TYPES = ["SINGLE_CHOICE", "MULTIPLE_CHOICE"];
const NEW_QUESTION_CHOICE_TYPES = ["SINGLE_CHOICE", "MULTIPLE_CHOICE"];
const EDITABLE_STATUSES = ["DRAFT"];

type OptionDraft = { label: string; image_url: string };
type PendingOption = { label: string };
type PendingImage = { url: string; label: string };

function emptyQuestionForm() {
  return {
    qTitle: "",
    qType: "TEXT",
    pendingOptions: [] as PendingOption[],
    pendingImages: [] as PendingImage[],
    pendingOptionDraft: { label: "", image_url: "" } as OptionDraft,
  };
}

function imageLabelFromFile(file: File, index: number) {
  const base = file.name.replace(/\.[^.]+$/, "").trim();
  return base || `Изображение ${index + 1}`;
}

function statusLabel(status: string) {
  switch (status) {
    case "DRAFT":
      return "Черновик";
    case "ACTIVE":
      return "Опубликован";
    default:
      return status;
  }
}

export default function SurveyEditor() {
  const { id } = useParams<{ id: string }>();
  const [survey, setSurvey] = useState<{ title: string; status: string } | null>(null);
  const [surveyTitle, setSurveyTitle] = useState("");
  const [questions, setQuestions] = useState<any[]>([]);
  const [links, setLinks] = useState<any[]>([]);
  const [qTitle, setQTitle] = useState("");
  const [qType, setQType] = useState("TEXT");
  const [pendingOptions, setPendingOptions] = useState<PendingOption[]>([]);
  const [pendingImages, setPendingImages] = useState<PendingImage[]>([]);
  const [pendingOptionDraft, setPendingOptionDraft] = useState<OptionDraft>({ label: "", image_url: "" });
  const [error, setError] = useState("");
  const [optionDrafts, setOptionDrafts] = useState<Record<string, OptionDraft>>({});
  const [uploadingImages, setUploadingImages] = useState(false);
  const [savingQuestion, setSavingQuestion] = useState(false);
  const [editingQuestionId, setEditingQuestionId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{ title: string; qType: string; required: boolean } | null>(
    null,
  );
  const [savingQuestionEdit, setSavingQuestionEdit] = useState(false);

  const isEditable = survey ? EDITABLE_STATUSES.includes(survey.status) : false;

  const resetQuestionForm = () => {
    const empty = emptyQuestionForm();
    setQTitle(empty.qTitle);
    setQType(empty.qType);
    setPendingOptions(empty.pendingOptions);
    setPendingImages(empty.pendingImages);
    setPendingOptionDraft(empty.pendingOptionDraft);
  };

  const load = useCallback(async () => {
    if (!id) return;
    const s = await api.getSurvey(id);
    setSurvey(s);
    setSurveyTitle(s.title);
    setQuestions(await api.getQuestions(id));
    setLinks(await api.getLinks(id));
  }, [id]);

  useEffect(() => {
    initCsrf().then(load).catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [load]);

  const getOptionDraft = (questionId: string): OptionDraft =>
    optionDrafts[questionId] ?? { label: "", image_url: "" };

  const setOptionDraft = (questionId: string, patch: Partial<OptionDraft>) => {
    setOptionDrafts((prev) => ({
      ...prev,
      [questionId]: { ...getOptionDraft(questionId), ...patch },
    }));
  };

  const saveSurveyTitle = async () => {
    if (!id || !isEditable || !surveyTitle.trim()) return;
    setError("");
    try {
      await api.updateSurvey(id, { title: surveyTitle.trim() });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const addPendingOption = () => {
    if (!pendingOptionDraft.label.trim()) {
      setError("Укажите текст варианта");
      return;
    }
    setError("");
    setPendingOptions((prev) => [...prev, { label: pendingOptionDraft.label.trim() }]);
    setPendingOptionDraft({ label: "", image_url: "" });
  };

  const removePendingOption = (index: number) => {
    setPendingOptions((prev) => prev.filter((_, i) => i !== index));
  };

  const removePendingImage = (index: number) => {
    setPendingImages((prev) => prev.filter((_, i) => i !== index));
  };

  const saveQuestion = async () => {
    if (!id || !isEditable || savingQuestion) return;
    if (!qTitle.trim()) {
      setError("Укажите название вопроса");
      return;
    }
    setError("");
    setSavingQuestion(true);
    try {
      const created = await api.createQuestion(id, {
        title: qTitle.trim(),
        question_type: qType,
        required: false,
        order: questions.length,
      });
      if (qType === "IMAGE_CHOICE") {
        for (let i = 0; i < pendingImages.length; i++) {
          await api.createOption(id, created.id, {
            label: pendingImages[i].label,
            image_url: pendingImages[i].url,
            order: i,
          });
        }
      } else if (NEW_QUESTION_CHOICE_TYPES.includes(qType)) {
        for (let i = 0; i < pendingOptions.length; i++) {
          await api.createOption(id, created.id, {
            label: pendingOptions[i].label,
            order: i,
          });
        }
      }
      resetQuestionForm();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingQuestion(false);
    }
  };

  const addQuestionField = () => {
    const hasContent =
      qTitle.trim() || pendingOptions.length > 0 || pendingImages.length > 0 || pendingOptionDraft.label.trim();
    if (hasContent) {
      const ok = confirm(
        "Очистить форму для нового вопроса? Несохранённые данные будут потеряны — сначала нажмите «Сохранить вопрос».",
      );
      if (!ok) return;
    }
    setError("");
    resetQuestionForm();
  };

  const attachImages = async (files: FileList | null, questionId?: string) => {
    if (!id || !files?.length || !isEditable) return;
    setError("");
    setUploadingImages(true);
    try {
      const fileList = Array.from(files).filter((f) => f.type.startsWith("image/"));
      if (!fileList.length) {
        setError("Выберите файл изображения");
        return;
      }
      const q = questionId ? questions.find((item) => item.id === questionId) : null;
      let order = q?.options?.length ?? pendingImages.length;
      const uploaded: PendingImage[] = [];
      for (const file of fileList) {
        const { url } = await api.uploadImage(id, file);
        const label = imageLabelFromFile(file, order);
        if (questionId) {
          await api.createOption(id, questionId, { label, image_url: url, order });
        } else {
          uploaded.push({ url, label });
        }
        order += 1;
      }
      if (questionId) {
        await load();
      } else if (uploaded.length) {
        setPendingImages((prev) => [...prev, ...uploaded]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploadingImages(false);
    }
  };

  const startEditQuestion = (q: any) => {
    setEditingQuestionId(q.id);
    setEditForm({ title: q.title, qType: q.question_type, required: q.required });
  };

  const cancelEditQuestion = () => {
    setEditingQuestionId(null);
    setEditForm(null);
  };

  const saveQuestionEdit = async (questionId: string) => {
    if (!id || !isEditable || !editForm?.title.trim() || savingQuestionEdit) return;
    setError("");
    setSavingQuestionEdit(true);
    try {
      await api.updateQuestion(id, questionId, {
        title: editForm.title.trim(),
        question_type: editForm.qType,
        required: editForm.required,
      });
      cancelEditQuestion();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingQuestionEdit(false);
    }
  };

  const updateOptionLabel = async (questionId: string, optionId: string, label: string) => {
    if (!id || !isEditable || !label.trim()) return;
    setError("");
    try {
      const trimmed = label.trim();
      await api.updateOption(id, questionId, optionId, { label: trimmed, value: trimmed });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const removeQuestion = async (questionId: string) => {
    if (!id || !isEditable) return;
    if (!confirm("Удалить вопрос?")) return;
    setError("");
    try {
      await api.deleteQuestion(id, questionId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const moveQuestion = async (index: number, direction: -1 | 1) => {
    if (!id || !isEditable) return;
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= questions.length) return;
    const current = questions[index];
    const target = questions[targetIndex];
    setError("");
    try {
      await api.updateQuestion(id, current.id, { order: target.order });
      await api.updateQuestion(id, target.id, { order: current.order });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const addOption = async (questionId: string) => {
    if (!id || !isEditable) return;
    const draft = getOptionDraft(questionId);
    if (!draft.label.trim()) {
      setError("Укажите текст варианта");
      return;
    }
    setError("");
    try {
      const q = questions.find((item) => item.id === questionId);
      const order = q?.options?.length ?? 0;
      await api.createOption(id, questionId, {
        label: draft.label.trim(),
        order,
      });
      setOptionDraft(questionId, { label: "", image_url: "" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const removeOption = async (questionId: string, optionId: string) => {
    if (!id || !isEditable) return;
    setError("");
    try {
      await api.deleteOption(id, questionId, optionId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const publish = async () => {
    if (!id) return;
    setError("");
    try {
      await api.updateSurvey(id, { status: "ACTIVE" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const unpublish = async () => {
    if (!id) return;
    if (!confirm("Снять опрос с публикации? Ссылки перестанут работать, но ответы сохранятся.")) return;
    setError("");
    try {
      await api.updateSurvey(id, { status: "DRAFT" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const createLink = async () => {
    if (!id) return;
    setError("");
    try {
      await api.createLink(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const exportXls = async () => {
    if (!id) return;
    const res = await fetch(api.exportUrl(id), {
      headers: { Authorization: `Bearer ${getAccessToken()}` },
      credentials: "include",
    });
    if (!res.ok) throw new Error("Export failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `survey_${id}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!survey) return <p>Загрузка...</p>;

  return (
    <>
      <div className="card">
        <h2>Редактор опроса</h2>
        <div className="field">
          <label>Название</label>
          <input
            value={surveyTitle}
            onChange={(e) => setSurveyTitle(e.target.value)}
            disabled={!isEditable}
          />
        </div>
        {isEditable && (
          <button className="secondary" onClick={saveSurveyTitle} style={{ marginBottom: 12 }}>
            Сохранить название
          </button>
        )}
        <p>
          Статус: <strong>{statusLabel(survey.status)}</strong>
          {survey.status === "ACTIVE" && (
            <span style={{ marginLeft: 8, color: "#b45309" }}>
              — снимите с публикации, чтобы редактировать вопросы
            </span>
          )}
          {survey.status === "DRAFT" && (
            <span style={{ marginLeft: 8, color: "#b45309" }}>
              — опубликуйте опрос, чтобы ссылка работала
            </span>
          )}
        </p>
        {survey.status !== "ACTIVE" && (
          <button onClick={publish}>Опубликовать</button>
        )}{" "}
        {survey.status === "ACTIVE" && (
          <button className="secondary" onClick={unpublish}>
            Снять с публикации
          </button>
        )}{" "}
        <button className="secondary" onClick={exportXls}>
          Скачать XLS
        </button>{" "}
        <Link to={`/surveys/${id}/responses`} className="button-link secondary">
          Ответы респондентов
        </Link>
      </div>

      <div className="card">
        <h3>Вопросы</h3>
        {!isEditable && (
          <p style={{ color: "#555", marginTop: 0 }}>
            Редактирование вопросов доступно только для неопубликованных опросов.
          </p>
        )}

        {questions.map((q, index) => (
          <div key={q.id} style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #eee" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 8, flexWrap: "wrap" }}>
              {isEditable && (
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <button
                    className="secondary"
                    style={{ padding: "4px 8px", fontSize: 12 }}
                    disabled={index === 0}
                    onClick={() => moveQuestion(index, -1)}
                    title="Переместить вверх"
                  >
                    ↑
                  </button>
                  <button
                    className="secondary"
                    style={{ padding: "4px 8px", fontSize: 12 }}
                    disabled={index === questions.length - 1}
                    onClick={() => moveQuestion(index, 1)}
                    title="Переместить вниз"
                  >
                    ↓
                  </button>
                </div>
              )}
              <div style={{ flex: 1, minWidth: 200 }}>
                {editingQuestionId === q.id && editForm && isEditable ? (
                  <div className="question-edit-panel">
                    <div className="field">
                      <label>Текст вопроса</label>
                      <input
                        value={editForm.title}
                        onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      />
                    </div>
                    <div className="field">
                      <label>Тип</label>
                      <select
                        value={editForm.qType}
                        onChange={(e) => setEditForm({ ...editForm, qType: e.target.value })}
                      >
                        <option value="TEXT">Свободный ответ</option>
                        <option value="SINGLE_CHOICE">Один вариант</option>
                        <option value="MULTIPLE_CHOICE">Несколько вариантов</option>
                        <option value="IMAGE_CHOICE">Выбор картинки</option>
                        <option value="IMAGE_UPLOAD">Загрузка картинки респондентом</option>
                        <option value="RATING">Рейтинг</option>
                        <option value="DATE">Дата</option>
                      </select>
                    </div>
                    <label className="choice-option" style={{ marginBottom: 12 }}>
                      <input
                        type="checkbox"
                        checked={editForm.required}
                        onChange={(e) => setEditForm({ ...editForm, required: e.target.checked })}
                      />
                      <span>Обязательный вопрос</span>
                    </label>
                    {questionHint(editForm.qType) && (
                      <p className="field-hint">{questionHint(editForm.qType)}</p>
                    )}
                    <button onClick={() => saveQuestionEdit(q.id)} disabled={savingQuestionEdit}>
                      {savingQuestionEdit ? "Сохранение..." : "Сохранить изменения"}
                    </button>{" "}
                    <button className="secondary" onClick={cancelEditQuestion}>
                      Отмена
                    </button>
                  </div>
                ) : (
                  <>
                    <strong>{q.title}</strong>
                    <span style={{ color: "#666", marginLeft: 8 }}>
                      ({questionTypeLabel(q.question_type)})
                      {q.required && " · обязательный"}
                    </span>
                    {questionHint(q.question_type) && (
                      <p className="field-hint" style={{ margin: "6px 0 0" }}>
                        {questionHint(q.question_type)}
                      </p>
                    )}
                    {isEditable && (
                      <>
                        <button
                          className="secondary"
                          style={{ marginLeft: 8, padding: "4px 8px", fontSize: 12 }}
                          onClick={() => startEditQuestion(q)}
                        >
                          Редактировать
                        </button>
                        <button
                          className="secondary"
                          style={{ marginLeft: 8, padding: "4px 8px", fontSize: 12 }}
                          onClick={() => removeQuestion(q.id)}
                        >
                          Удалить
                        </button>
                      </>
                    )}
                  </>
                )}
              </div>
            </div>

            {q.question_type === "IMAGE_UPLOAD" && (
              <div style={{ marginTop: 12, padding: 12, background: "#f0f7ff", borderRadius: 8, color: "#444" }}>
                Респондент прикрепит своё изображение при прохождении опроса. Настройка вариантов не требуется.
              </div>
            )}

            {q.question_type === "IMAGE_CHOICE" && (
              <div style={{ marginTop: 12, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
                <h4 style={{ margin: "0 0 12px" }}>Картинки для выбора</h4>
                <div className="image-grid">
                  {q.options?.map((o: any) => (
                    <div key={o.id} className="image-card">
                      <img src={o.image_url} alt={o.label} />
                      {isEditable && editingQuestionId === q.id ? (
                        <input
                          defaultValue={o.label}
                          onBlur={(e) => {
                            if (e.target.value.trim() !== o.label) {
                              updateOptionLabel(q.id, o.id, e.target.value);
                            }
                          }}
                          style={{ width: "100%", marginTop: 4 }}
                        />
                      ) : (
                        <span>{o.label}</span>
                      )}
                      {isEditable && (
                        <button className="secondary" onClick={() => removeOption(q.id, o.id)}>
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                {(!q.options || q.options.length === 0) && (
                  <p style={{ color: "#666", margin: "0 0 12px" }}>
                    Прикрепите минимум 2 картинки перед публикацией
                  </p>
                )}
                {isEditable && editingQuestionId !== q.id && (
                  <label className="file-input-label">
                    {uploadingImages ? "Загрузка..." : "Прикрепить картинку"}
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/gif,image/webp"
                      multiple
                      disabled={uploadingImages}
                      onChange={(e) => {
                        attachImages(e.target.files, q.id);
                        e.target.value = "";
                      }}
                    />
                  </label>
                )}
              </div>
            )}

            {TEXT_CHOICE_TYPES.includes(q.question_type) && (
              <div style={{ marginTop: 12, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
                <h4 style={{ margin: "0 0 12px" }}>Варианты ответа</h4>
                <ul style={{ margin: "0 0 12px", paddingLeft: 20 }}>
                  {q.options?.map((o: any) => (
                    <li key={o.id} style={{ marginBottom: 6 }}>
                      {isEditable && editingQuestionId === q.id ? (
                        <input
                          defaultValue={o.label}
                          onBlur={(e) => {
                            if (e.target.value.trim() !== o.label) {
                              updateOptionLabel(q.id, o.id, e.target.value);
                            }
                          }}
                          style={{ maxWidth: 280 }}
                        />
                      ) : (
                        o.label
                      )}
                      {isEditable && (
                        <button
                          className="secondary"
                          style={{ marginLeft: 8, padding: "4px 8px", fontSize: 12 }}
                          onClick={() => removeOption(q.id, o.id)}
                        >
                          Удалить
                        </button>
                      )}
                    </li>
                  ))}
                  {(!q.options || q.options.length === 0) && (
                    <li style={{ color: "#666" }}>Добавьте минимум 2 варианта перед публикацией</li>
                  )}
                </ul>
                {isEditable && (
                  <>
                    <div className="field">
                      <label>Текст варианта</label>
                      <input
                        value={getOptionDraft(q.id).label}
                        onChange={(e) => setOptionDraft(q.id, { label: e.target.value })}
                        placeholder="Например: Да"
                      />
                    </div>
                    <button className="secondary" onClick={() => addOption(q.id)}>
                      + Добавить вариант
                    </button>
                    {editingQuestionId === q.id && (
                      <p className="field-hint" style={{ margin: "8px 0 0" }}>
                        Текст существующих вариантов сохраняется при выходе из поля.
                      </p>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        ))}

        {isEditable && (
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #eee" }}>
            <h4 style={{ margin: "0 0 12px" }}>Новый вопрос</h4>
            <div className="field">
              <label>Текст вопроса</label>
              <input
                value={qTitle}
                onChange={(e) => setQTitle(e.target.value)}
                placeholder="Название вопроса"
              />
            </div>
            <div className="field">
              <label>Тип</label>
              <select
                value={qType}
                onChange={(e) => {
                  const nextType = e.target.value;
                  setQType(nextType);
                  if (!NEW_QUESTION_CHOICE_TYPES.includes(nextType)) {
                    setPendingOptions([]);
                    setPendingOptionDraft({ label: "", image_url: "" });
                  }
                  if (nextType !== "IMAGE_CHOICE") {
                    setPendingImages([]);
                  }
                }}
              >
                <option value="TEXT">Свободный ответ</option>
                <option value="SINGLE_CHOICE">Один вариант</option>
                <option value="MULTIPLE_CHOICE">Несколько вариантов</option>
                <option value="IMAGE_CHOICE">Выбор картинки</option>
                <option value="IMAGE_UPLOAD">Загрузка картинки респондентом</option>
                <option value="RATING">Рейтинг</option>
                <option value="DATE">Дата</option>
              </select>
            </div>
            {questionHint(qType) && <p className="field-hint">{questionHint(qType)}</p>}
            {qType === "IMAGE_UPLOAD" && (
              <div style={{ marginBottom: 16, padding: 12, background: "#f0f7ff", borderRadius: 8, color: "#444" }}>
                Респондент прикрепит своё изображение при прохождении опроса.
              </div>
            )}
            {qType === "IMAGE_CHOICE" && (
              <div style={{ marginBottom: 16, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
                <h4 style={{ margin: "0 0 12px" }}>Картинки для выбора</h4>
                <div className="image-grid">
                  {pendingImages.map((img, index) => (
                    <div key={`${img.url}-${index}`} className="image-card">
                      <img src={img.url} alt={img.label} />
                      <span>{img.label}</span>
                      <button className="secondary" onClick={() => removePendingImage(index)}>
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
                {pendingImages.length === 0 && (
                  <p style={{ color: "#666", margin: "0 0 12px" }}>
                    Прикрепите минимум 2 картинки перед публикацией
                  </p>
                )}
                <label className="file-input-label">
                  {uploadingImages ? "Загрузка..." : "Прикрепить картинку"}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    multiple
                    disabled={uploadingImages}
                    onChange={(e) => {
                      attachImages(e.target.files);
                      e.target.value = "";
                    }}
                  />
                </label>
              </div>
            )}

            {NEW_QUESTION_CHOICE_TYPES.includes(qType) && (
              <div style={{ marginBottom: 16, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
                <h4 style={{ margin: "0 0 12px" }}>Варианты ответа</h4>
                <ul style={{ margin: "0 0 12px", paddingLeft: 20 }}>
                  {pendingOptions.map((o, index) => (
                    <li key={`${o.label}-${index}`} style={{ marginBottom: 6 }}>
                      {o.label}
                      <button
                        className="secondary"
                        style={{ marginLeft: 8, padding: "4px 8px", fontSize: 12 }}
                        onClick={() => removePendingOption(index)}
                      >
                        Удалить
                      </button>
                    </li>
                  ))}
                  {pendingOptions.length === 0 && (
                    <li style={{ color: "#666" }}>Добавьте минимум 2 варианта перед публикацией</li>
                  )}
                </ul>
                <div className="field">
                  <label>Текст варианта</label>
                  <input
                    value={pendingOptionDraft.label}
                    onChange={(e) => setPendingOptionDraft({ ...pendingOptionDraft, label: e.target.value })}
                    placeholder="Например: Да"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addPendingOption();
                      }
                    }}
                  />
                </div>
                <button className="secondary" onClick={addPendingOption}>
                  + Добавить вариант
                </button>
              </div>
            )}
            <button onClick={saveQuestion} disabled={savingQuestion}>
              {savingQuestion ? "Сохранение..." : "Сохранить вопрос"}
            </button>{" "}
            <button className="secondary" onClick={addQuestionField}>
              Добавить вопрос
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h3>Публичные ссылки</h3>
        <button onClick={createLink}>Создать ссылку и опубликовать</button>
        {links.length === 0 ? (
          <p style={{ color: "#666", marginTop: 12 }}>Активных ссылок пока нет</p>
        ) : (
          <ul>
            {links.map((l) => (
              <li key={l.id}>
                <a href={l.public_url} target="_blank" rel="noreferrer">
                  {l.public_url}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
      {error && <p className="error">{error}</p>}
    </>
  );
}
