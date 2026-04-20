"use client";

import React, { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center shadow-apple">
          <p className="text-sm font-medium text-red-700">
            {this.props.fallbackMessage ?? "Algo deu errado ao carregar este componente."}
          </p>
          {this.state.error && (
            <p className="mt-2 text-xs text-red-500">{this.state.error.message}</p>
          )}
          <button
            onClick={this.handleRetry}
            className="mt-4 rounded-full bg-red-600 px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700"
          >
            Tentar novamente
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
