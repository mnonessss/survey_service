import { useEffect } from "react";
import { Link, Route, Routes, useNavigate } from "react-router-dom";
import { AuthProvider, RequireAuth, useAuth } from "./auth/AuthContext";
import { initCsrf, setAccessToken } from "./api/client";
import Dashboard from "./pages/Dashboard";
import SurveyEditor from "./pages/SurveyEditor";
import SurveyResponses from "./pages/SurveyResponses";
import PublicSurvey from "./pages/PublicSurvey";

function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauthError = params.get("error");
    if (oauthError) return;

    const token = params.get("access_token");
    if (!token) return;

    setAccessToken(token);
    initCsrf()
      .then(() => navigate("/", { replace: true }))
      .catch(() => navigate("/", { replace: true }));
  }, [navigate]);

  const params = new URLSearchParams(window.location.search);
  const oauthError = params.get("error");
  if (oauthError) {
    return (
      <div className="container card error">
        <p>{params.get("error_description") || oauthError}</p>
      </div>
    );
  }

  return (
    <div className="container">
      <p>Вход выполняется...</p>
    </div>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  const { userEmail } = useAuth();

  return (
    <div className="container">
      <div className="header">
        <h1>Survey Platform</h1>
        <div>
          {userEmail && <span style={{ marginRight: 12 }}>{userEmail}</span>}
          <Link to="/">Опросы</Link>
        </div>
      </div>
      {children}
    </div>
  );
}

function Protected({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <Layout>{children}</Layout>
    </RequireAuth>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/s/:token" element={<PublicSurvey />} />
        <Route
          path="/"
          element={
            <Protected>
              <Dashboard />
            </Protected>
          }
        />
        <Route
          path="/surveys/:id"
          element={
            <Protected>
              <SurveyEditor />
            </Protected>
          }
        />
        <Route
          path="/surveys/:id/responses"
          element={
            <Protected>
              <SurveyResponses />
            </Protected>
          }
        />
      </Routes>
    </AuthProvider>
  );
}
