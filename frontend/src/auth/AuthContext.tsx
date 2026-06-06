import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { api, getAccessToken, initCsrf, setAccessToken } from "../api/client";

type AuthStatus = "loading" | "authenticated" | "redirecting" | "denied";

type AuthContextValue = {
  status: AuthStatus;
  userEmail: string;
  error: string;
};

const AuthContext = createContext<AuthContextValue>({
  status: "loading",
  userEmail: "",
  error: "",
});

export function useAuth() {
  return useContext(AuthContext);
}

function isPublicPath(pathname: string) {
  return pathname.startsWith("/s/") || pathname.startsWith("/auth/callback");
}

async function redirectToLogin() {
  const { authorization_url } = await api.loginInit();
  window.location.href = authorization_url;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [userEmail, setUserEmail] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (isPublicPath(location.pathname)) {
      setStatus("authenticated");
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setStatus("redirecting");
      redirectToLogin().catch((e) => {
        setError(e instanceof Error ? e.message : String(e));
        setStatus("denied");
      });
      return;
    }

    initCsrf()
      .then(() => api.getMe())
      .then((user) => {
        setUserEmail(user.email);
        setStatus("authenticated");
      })
      .catch(() => {
        setAccessToken("");
        setStatus("redirecting");
        redirectToLogin().catch((err) => {
          setError(err instanceof Error ? err.message : String(err));
          setStatus("denied");
        });
      });
  }, [location.pathname]);

  return (
    <AuthContext.Provider value={{ status, userEmail, error }}>{children}</AuthContext.Provider>
  );
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { status, error } = useAuth();

  if (status === "loading" || status === "redirecting") {
    return (
      <div className="container">
        <p>{status === "redirecting" ? "Перенаправление на auth.vk.team..." : "Загрузка..."}</p>
      </div>
    );
  }

  if (status !== "authenticated") {
    return (
      <div className="container">
        <div className="card error">
          <p>{error || "Не удалось войти через auth.vk.team."}</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
