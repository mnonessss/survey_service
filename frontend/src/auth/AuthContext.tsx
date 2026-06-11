import { useEffect, useState, type ReactNode } from "react";
import { Panel, Placeholder, Spinner } from "@vkontakte/vkui";
import { useLocation } from "react-router-dom";
import { api, getAccessToken, initCsrf, setAccessToken } from "../api/client";
import { AuthContext, type AuthStatus } from "./authContextState";
import { useAuth } from "./useAuth";
import { parseVkLaunchParams } from "./vkLaunchParams";

function isPublicPath(pathname: string) {
  return pathname.startsWith("/s/");
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

    const authenticate = async () => {
      if (!getAccessToken()) {
        const launchParams = parseVkLaunchParams();
        if (launchParams) {
          const res = await api.silentAuth(launchParams);
          if (res.status !== "success" || !res.access_token) {
            throw new Error("Не удалось выполнить авторизацию");
          }
          setAccessToken(res.access_token);
        }
      }

      await initCsrf();
      const user = await api.getMe();
      setUserEmail(user.email);
      setStatus("authenticated");
    };

    authenticate().catch((e) => {
      setError(e instanceof Error ? e.message : String(e));
      setStatus("denied");
    });
  }, [location.pathname]);

  return (
    <AuthContext.Provider value={{ status, userEmail, error }}>{children}</AuthContext.Provider>
  );
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { status, error } = useAuth();

  if (status === "loading") {
    return (
      <Panel>
        <Placeholder>
          <Spinner size="l" />
          Авторизация...
        </Placeholder>
      </Panel>
    );
  }

  if (status !== "authenticated") {
    return (
      <Panel>
        <Placeholder title="Доступ ограничен">
          {error || "Откройте приложение через VK Mini Apps."}
        </Placeholder>
      </Panel>
    );
  }

  return <>{children}</>;
}
