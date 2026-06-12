import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Banner,
  Button,
  Checkbox,
  FormItem,
  Group,
  Header,
  IconButton,
  Input,
  Placeholder,
  Separator,
  SimpleCell,
  Spinner,
  Title,
} from "@vkontakte/vkui";
import { Icon24ChevronDown, Icon24ChevronUp, Icon24DeleteOutline } from "@vkontakte/icons";
import { api, getAccessToken, initCsrf } from "../api/client";
import { QuestionTypeSelect } from "../components/QuestionTypeSelect";
import { questionTypeLabel } from "../utils/questionHints";

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
    qRequired: false,
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
  const navigate = useNavigate();
  const [survey, setSurvey] = useState<{
    title: string;
    status: string;
    has_been_published?: boolean;
  } | null>(null);
  const [surveyTitle, setSurveyTitle] = useState("");
  const [questions, setQuestions] = useState<any[]>([]);
  const [links, setLinks] = useState<any[]>([]);
  const [qTitle, setQTitle] = useState("");
  const [qType, setQType] = useState("TEXT");
  const [qRequired, setQRequired] = useState(false);
  const [pendingOptions, setPendingOptions] = useState<PendingOption[]>([]);
  const [pendingImages, setPendingImages] = useState<PendingImage[]>([]);
  const [pendingOptionDraft, setPendingOptionDraft] = useState<OptionDraft>({ label: "", image_url: "" });
  const [error, setError] = useState("");
  const [optionDrafts, setOptionDrafts] = useState<Record<string, OptionDraft>>({});
  const [uploadingImages, setUploadingImages] = useState(false);
  const [savingQuestion, setSavingQuestion] = useState(false);
  const [editingQuestionId, setEditingQuestionId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{ title: string; qType: string; required: boolean } | null>(null);
  const [savingQuestionEdit, setSavingQuestionEdit] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const questionFileRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const isEditable = survey ? EDITABLE_STATUSES.includes(survey.status) : false;

  const resetQuestionForm = () => {
    const empty = emptyQuestionForm();
    setQTitle(empty.qTitle);
    setQType(empty.qType);
    setQRequired(empty.qRequired);
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
        required: qRequired,
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
      await api.createOption(id, questionId, { label: draft.label.trim(), order });
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

  const wasEverPublished = Boolean(survey?.has_been_published);

  const requirePublished = (action: () => void) => {
    if (!wasEverPublished) {
      setError("Сначала опубликуйте опрос — нажмите «Создать ссылку и опубликовать».");
      return;
    }
    action();
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
    if (!surveyTitle.trim()) {
      setError("Укажите название опроса");
      return;
    }
    setError("");
    try {
      if (isEditable && surveyTitle.trim() !== survey?.title) {
        await api.updateSurvey(id, { title: surveyTitle.trim() });
      }
      await api.createLink(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const exportXls = async () => {
    if (!id) return;
    setError("");
    try {
      const res = await fetch(api.exportUrl(id), {
        headers: { Authorization: `Bearer ${getAccessToken()}` },
        credentials: "include",
      });
      if (!res.ok) throw new Error("Не удалось скачать файл");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `survey_${id}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const openResponses = () => {
    if (!id) return;
    navigate(`/surveys/${id}/responses`);
  };

  if (!survey) {
    return (
      <Placeholder>
        <Spinner size="l" />
      </Placeholder>
    );
  }

  return (
    <>
      <Group header={<Header size="s">Редактор опроса</Header>}>
        <FormItem top="Название">
          <Input
            value={surveyTitle}
            onChange={(e) => setSurveyTitle(e.target.value)}
            disabled={!isEditable}
          />
        </FormItem>
        <FormItem top="Статус">
          <Title level="3" weight="2">
            {statusLabel(survey.status)}
          </Title>
        </FormItem>
        {survey.status === "ACTIVE" && (
          <Banner mode="tint" before={null}>
            Снимите с публикации, чтобы редактировать вопросы
          </Banner>
        )}
        {survey.status === "DRAFT" && (
          <Banner mode="tint" before={null}>
            Создайте ссылку, чтобы опубликовать опрос
          </Banner>
        )}
      </Group>

      <Group header={<Header size="s">Вопросы</Header>}>
        {!isEditable && (
          <Banner mode="tint" before={null}>
            Редактирование вопросов доступно только для неопубликованных опросов
          </Banner>
        )}

        {questions.map((q, index) => (
          <div key={q.id}>
            <Separator />
            <div className="vk-question-row">
              {isEditable && (
                <div className="vk-question-move">
                  <IconButton onClick={() => moveQuestion(index, -1)} disabled={index === 0} aria-label="Вверх">
                    <Icon24ChevronUp />
                  </IconButton>
                  <IconButton
                    onClick={() => moveQuestion(index, 1)}
                    disabled={index === questions.length - 1}
                    aria-label="Вниз"
                  >
                    <Icon24ChevronDown />
                  </IconButton>
                </div>
              )}
              <div className="vk-question-body">
                {editingQuestionId === q.id && editForm && isEditable ? (
                  <Group>
                    <FormItem top="Текст вопроса">
                      <Input
                        value={editForm.title}
                        onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      />
                    </FormItem>
                    <FormItem top="Тип">
                      <QuestionTypeSelect
                        value={editForm.qType}
                        onChange={(v) => setEditForm({ ...editForm, qType: v })}
                      />
                    </FormItem>
                    <Checkbox
                      checked={editForm.required}
                      onChange={(e) => setEditForm({ ...editForm, required: e.target.checked })}
                    >
                      Обязательный вопрос
                    </Checkbox>
                    <FormItem>
                      <Button onClick={() => saveQuestionEdit(q.id)} loading={savingQuestionEdit}>
                        Сохранить изменения
                      </Button>
                      {" "}
                      <Button mode="secondary" onClick={cancelEditQuestion}>
                        Отмена
                      </Button>
                    </FormItem>
                  </Group>
                ) : (
                  <>
                    <Title level="2" weight="2">
                      {q.title}
                    </Title>
                    <Title level="3" weight="3">
                      {questionTypeLabel(q.question_type)}
                      {q.required && " · обязательный"}
                    </Title>
                    {isEditable && (
                      <FormItem>
                        <Button mode="secondary" size="s" onClick={() => startEditQuestion(q)}>
                          Редактировать
                        </Button>
                        {" "}
                        <IconButton onClick={() => removeQuestion(q.id)} aria-label="Удалить">
                          <Icon24DeleteOutline />
                        </IconButton>
                      </FormItem>
                    )}
                  </>
                )}

                {q.question_type === "IMAGE_UPLOAD" && (
                  <Banner mode="tint" before={null}>
                    Респондент прикрепит одно изображение при прохождении опроса
                  </Banner>
                )}

                {q.question_type === "IMAGE_UPLOAD_MULTIPLE" && (
                  <Banner mode="tint" before={null}>
                    Респондент сможет прикрепить несколько изображений при прохождении опроса
                  </Banner>
                )}

                {q.question_type === "IMAGE_CHOICE" && (
                  <Group header={<Header size="s">Картинки для выбора</Header>}>
                    <div className="vk-image-choice-grid">
                      {q.options?.map((o: any) => (
                        <div key={o.id} className="vk-image-choice-item">
                          <img src={o.image_url} alt={o.label} />
                          {isEditable && editingQuestionId === q.id ? (
                            <Input
                              defaultValue={o.label}
                              onBlur={(e) => {
                                if (e.target.value.trim() !== o.label) {
                                  updateOptionLabel(q.id, o.id, e.target.value);
                                }
                              }}
                            />
                          ) : (
                            <span>{o.label}</span>
                          )}
                          {isEditable && (
                            <Button mode="secondary" size="s" onClick={() => removeOption(q.id, o.id)}>
                              Удалить
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                    {(!q.options || q.options.length === 0) && (
                      <Placeholder>Прикрепите минимум 2 картинки перед публикацией</Placeholder>
                    )}
                    {isEditable && editingQuestionId !== q.id && (
                      <>
                        <input
                          type="file"
                          accept="image/*"
                          multiple
                          hidden
                          ref={(el) => {
                            questionFileRefs.current[q.id] = el;
                          }}
                          onChange={(e) => {
                            attachImages(e.target.files, q.id);
                            e.target.value = "";
                          }}
                        />
                        <FormItem>
                          <Button
                            mode="secondary"
                            stretched
                            loading={uploadingImages}
                            onClick={() => questionFileRefs.current[q.id]?.click()}
                          >
                            Прикрепить картинку
                          </Button>
                        </FormItem>
                      </>
                    )}
                  </Group>
                )}

                {TEXT_CHOICE_TYPES.includes(q.question_type) && (
                  <Group header={<Header size="s">Варианты ответа</Header>}>
                    {q.options?.map((o: any) => (
                      <SimpleCell
                        key={o.id}
                        after={
                          isEditable ? (
                            <IconButton onClick={() => removeOption(q.id, o.id)} aria-label="Удалить">
                              <Icon24DeleteOutline />
                            </IconButton>
                          ) : undefined
                        }
                      >
                        {isEditable && editingQuestionId === q.id ? (
                          <Input
                            defaultValue={o.label}
                            onBlur={(e) => {
                              if (e.target.value.trim() !== o.label) {
                                updateOptionLabel(q.id, o.id, e.target.value);
                              }
                            }}
                          />
                        ) : (
                          o.label
                        )}
                      </SimpleCell>
                    ))}
                    {(!q.options || q.options.length === 0) && (
                      <Placeholder>Добавьте минимум 2 варианта перед публикацией</Placeholder>
                    )}
                    {isEditable && (
                      <>
                        <FormItem top="Текст варианта">
                          <Input
                            value={getOptionDraft(q.id).label}
                            onChange={(e) => setOptionDraft(q.id, { label: e.target.value })}
                            placeholder="Например: Да"
                          />
                        </FormItem>
                        <FormItem>
                          <Button mode="secondary" stretched onClick={() => addOption(q.id)}>
                            Добавить вариант
                          </Button>
                        </FormItem>
                      </>
                    )}
                  </Group>
                )}
              </div>
            </div>
          </div>
        ))}

        {isEditable && (
          <Group header={<Header size="s">Новый вопрос</Header>}>
            <FormItem top="Текст вопроса">
              <Input value={qTitle} onChange={(e) => setQTitle(e.target.value)} placeholder="Название вопроса" />
            </FormItem>
            <FormItem top="Тип">
              <QuestionTypeSelect
                value={qType}
                onChange={(nextType) => {
                  setQType(nextType);
                  if (!NEW_QUESTION_CHOICE_TYPES.includes(nextType)) {
                    setPendingOptions([]);
                    setPendingOptionDraft({ label: "", image_url: "" });
                  }
                  if (nextType !== "IMAGE_CHOICE") {
                    setPendingImages([]);
                  }
                }}
              />
            </FormItem>
            <Checkbox checked={qRequired} onChange={(e) => setQRequired(e.target.checked)}>
              Обязательный вопрос
            </Checkbox>

            {qType === "IMAGE_CHOICE" && (
              <Group header={<Header size="s">Картинки для выбора</Header>}>
                <div className="vk-image-choice-grid">
                  {pendingImages.map((img, index) => (
                    <div key={`${img.url}-${index}`} className="vk-image-choice-item">
                      <img src={img.url} alt={img.label} />
                      <span>{img.label}</span>
                      <Button mode="secondary" size="s" onClick={() => removePendingImage(index)}>
                        Удалить
                      </Button>
                    </div>
                  ))}
                </div>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  hidden
                  ref={fileInputRef}
                  onChange={(e) => {
                    attachImages(e.target.files);
                    e.target.value = "";
                  }}
                />
                <FormItem>
                  <Button
                    size="s"
                    stretched
                    loading={uploadingImages}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Прикрепить картинку
                  </Button>
                </FormItem>
              </Group>
            )}

            {NEW_QUESTION_CHOICE_TYPES.includes(qType) && (
              <Group header={<Header size="s">Варианты ответа</Header>}>
                {pendingOptions.map((o, index) => (
                  <SimpleCell
                    key={`${o.label}-${index}`}
                    after={
                      <Button mode="secondary" size="s" onClick={() => removePendingOption(index)}>
                        Удалить
                      </Button>
                    }
                  >
                    {o.label}
                  </SimpleCell>
                ))}
                <FormItem top="Текст варианта">
                  <Input
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
                </FormItem>
                <FormItem>
                  <Button mode="secondary" stretched onClick={addPendingOption}>
                    Добавить вариант
                  </Button>
                </FormItem>
              </Group>
            )}

            <FormItem>
              <Button stretched onClick={saveQuestion} loading={savingQuestion}>
                Сохранить вопрос
              </Button>
            </FormItem>
            <FormItem>
              <Button mode="secondary" stretched onClick={addQuestionField}>
                Очистить форму
              </Button>
            </FormItem>
          </Group>
        )}
      </Group>

      <Group header={<Header size="s">Публичные ссылки</Header>}>
        <FormItem>
          <Button stretched onClick={createLink}>
            Создать ссылку и опубликовать
          </Button>
        </FormItem>
        {survey.status === "ACTIVE" && (
          <FormItem>
            <Button mode="secondary" stretched onClick={unpublish}>
              Снять с публикации
            </Button>
          </FormItem>
        )}
        {links.length === 0 ? (
          <Placeholder>Активных ссылок пока нет</Placeholder>
        ) : (
          links.map((l) => (
            <SimpleCell key={l.id} subtitle={l.public_url} href={l.public_url} target="_blank">
              Ссылка на опрос
            </SimpleCell>
          ))
        )}
      </Group>

      <Group header={<Header size="s">Ответы</Header>}>
        <FormItem>
          <Button mode="secondary" stretched onClick={() => requirePublished(() => void exportXls())}>
            Скачать XLS
          </Button>
        </FormItem>
        <FormItem>
          <Button mode="secondary" stretched onClick={() => requirePublished(openResponses)}>
            Ответы респондентов
          </Button>
        </FormItem>
      </Group>

      {error && (
        <Group>
          <FormItem>
            <Title level="3" style={{ color: "var(--vkui--color_text_negative)" }}>
              {error}
            </Title>
          </FormItem>
        </Group>
      )}
    </>
  );
}
