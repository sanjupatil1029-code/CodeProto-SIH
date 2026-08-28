import { Component, type ReactNode } from "react";

interface Props { children: ReactNode; }
interface State { error: Error | null; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Unhandled error in app:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-mist p-6 text-center">
          <h1 className="font-display text-xl font-bold text-navy">Something went wrong</h1>
          <p className="mt-2 max-w-sm text-sm text-slate-soft">
            Please try again. If this keeps happening, refresh the page.
          </p>
          <button
            onClick={() => {
              this.setState({ error: null });
              window.location.reload();
            }}
            className="btn-primary mt-5 text-sm"
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
