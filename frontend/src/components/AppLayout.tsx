import { Icon24PollOutline } from "@vkontakte/icons";
import { Avatar, Panel, PanelHeader, PanelHeaderContent, Spacing } from "@vkontakte/vkui";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { userEmail } = useAuth();
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <Panel id="main">
      <PanelHeader
        before={<Avatar size={28}><Icon24PollOutline /></Avatar>}
        after={
          userEmail ? (
            <span style={{ fontSize: 13, opacity: 0.8, maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis" }}>
              {userEmail}
            </span>
          ) : undefined
        }
      >
        <PanelHeaderContent>
          {isHome ? (
            "Опросы"
          ) : (
            <Link to="/" style={{ color: "inherit", textDecoration: "none" }}>
              Опросы
            </Link>
          )}
        </PanelHeaderContent>
      </PanelHeader>
      <Spacing size={8} />
      {children}
    </Panel>
  );
}
