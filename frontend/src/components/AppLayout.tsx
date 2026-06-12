import { Icon24PollOutline } from "@vkontakte/icons";
import { Avatar, Panel, PanelHeader, PanelHeaderContent, Spacing } from "@vkontakte/vkui";
import { Link, useLocation } from "react-router-dom";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <Panel id="main">
      <PanelHeader before={<Avatar size={28}><Icon24PollOutline /></Avatar>}>
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
