import { Component, type ErrorInfo, type ReactNode } from "react";
import { Alert, Button, Group } from "@mantine/core";
import { TbAlertTriangle } from "react-icons/tb";

interface Props {
  pluginName: string;
  /** Changing this value clears a previous failure (e.g. after a lazy-chunk error). */
  resetKey?: unknown;
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Keeps one plugin's broken UI from taking down the page it is rendered on — the
 * frontend counterpart to the backend's plugin failure isolation.
 */
class ExtensionErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(
      `[plugins] Extension from "${this.props.pluginName}" crashed:`,
      error,
      info.componentStack
    );
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <Alert
        color="red"
        variant="light"
        icon={<TbAlertTriangle size={18} />}
        title={`${this.props.pluginName} section failed to render`}
        my="md"
      >
        <Group justify="space-between" align="center">
          {this.state.error.message}
          <Button
            size="xs"
            variant="default"
            onClick={() => this.setState({ error: null })}
          >
            Retry
          </Button>
        </Group>
      </Alert>
    );
  }
}

export default ExtensionErrorBoundary;
