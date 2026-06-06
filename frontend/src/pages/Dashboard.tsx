import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, initCsrf } from "../api/client";

type Survey = { id: string; title: string; status: string };

export default function Dashboard() {
  const navigate = useNavigate();
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  const load = () => api.getSurveys().then(setSurveys).catch((e) => setError(String(e)));

  useEffect(() => {
    initCsrf().then(load).catch((e) => setError(String(e)));
  }, []);

  const create = async () => {
    if (!title.trim()) return;
    setError("");
    try {
      const survey = await api.createSurvey({ title: title.trim(), description: "" });
      navigate(`/surveys/${survey.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <div className="card">
        <h2>Новый опрос</h2>
        <div className="field">
          <label>Название</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <button onClick={create}>Создать опрос</button>
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h2>Мои опросы</h2>
        {surveys.length === 0 && <p>Пока нет опросов</p>}
        <ul>
          {surveys.map((s) => (
            <li key={s.id}>
              <Link to={`/surveys/${s.id}`}>
                {s.title} ({s.status})
              </Link>
              {" · "}
              <Link to={`/surveys/${s.id}/responses`}>Ответы</Link>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
