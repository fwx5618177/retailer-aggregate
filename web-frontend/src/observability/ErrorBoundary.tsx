/**
 * Global error boundary that catches unhandled React errors.
 *
 * Reports errors to the configured error reporting service (Sentry DSN or
 * console fallback) and shows a user-friendly fallback UI.
 */
import { Component, type ErrorInfo, type ReactNode } from "react";
import { reportError } from "./reporter";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportError(error, { componentStack: info.componentStack ?? undefined });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md p-8 text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">
              应用发生错误
            </h1>
            <p className="text-gray-600 mb-6">
              {this.state.error?.message ?? "未知错误"}
            </p>
            <button
              className="px-4 py-2 bg-primary text-white rounded-lg"
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.href = "/";
              }}
            >
              返回首页
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
