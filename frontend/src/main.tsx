import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import bridge from "@vkontakte/vk-bridge";
import { AdaptivityProvider, AppRoot, ConfigProvider } from "@vkontakte/vkui";
import "@vkontakte/vkui/dist/vkui.css";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./styles.css";

// VK Mini Apps: без VKWebAppInit клиент VK показывает «Приложение не инициализировано»
const vkBridge = (bridge as { default?: typeof bridge }).default ?? bridge;
if (typeof vkBridge.send === "function") {
  void vkBridge.send("VKWebAppInit");
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider colorScheme="light">
      <AdaptivityProvider>
        <AppRoot mode="full">
          <ErrorBoundary>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </ErrorBoundary>
        </AppRoot>
      </AdaptivityProvider>
    </ConfigProvider>
  </React.StrictMode>,
);
