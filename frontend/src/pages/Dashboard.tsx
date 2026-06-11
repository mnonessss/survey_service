import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  FormItem,
  Group,
  Header,
  Input,
  Placeholder,
  SimpleCell,
  Spacing,
  Title,
} from "@vkontakte/vkui";
import { api, initCsrf } from "../api/client";

type Survey = { id: string; title: string; status: string };

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

export default function Dashboard() {
  const navigate = useNavigate();
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => api.getSurveys().then(setSurveys).catch((e) => setError(String(e)));

  useEffect(() => {
    initCsrf().then(load).catch((e) => setError(String(e)));
  }, []);

  const create = async () => {
    if (!title.trim() || creating) return;
    setError("");
    setCreating(true);
    try {
      const survey = await api.createSurvey({ title: title.trim(), description: "" });
      navigate(`/surveys/${survey.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  };

  return (
    <>
      <Group header={<Header size="s">Новый опрос</Header>}>
        <FormItem top="Название">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Например: Удовлетворённость сервисом"
          />
        </FormItem>
        <FormItem>
          <Button size="l" stretched onClick={create} loading={creating} disabled={!title.trim()}>
            Создать опрос
          </Button>
        </FormItem>
        {error && (
          <FormItem>
            <Title level="3" style={{ color: "var(--vkui--color_text_negative)" }}>
              {error}
            </Title>
          </FormItem>
        )}
      </Group>

      <Spacing size={12} />

      <Group header={<Header size="s">Мои опросы</Header>}>
        {surveys.length === 0 ? (
          <Placeholder>Пока нет опросов</Placeholder>
        ) : (
          surveys.map((s) => (
            <SimpleCell
              key={s.id}
              subtitle={statusLabel(s.status)}
              onClick={() => navigate(`/surveys/${s.id}`)}
              chevron="always"
              multiline
            >
              {s.title}
            </SimpleCell>
          ))
        )}
      </Group>
    </>
  );
}
