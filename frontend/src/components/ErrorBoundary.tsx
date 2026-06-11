import { Component, type ErrorInfo, type ReactNode } from "react";
import { Panel, Placeholder } from "@vkontakte/vkui";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <Panel>
          <Placeholder title="Ошибка интерфейса">{this.state.error.message}</Placeholder>
        </Panel>
      );
    }

    return this.props.children;
  }
}
