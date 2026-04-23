import surfaceOptions from './analyze_surface_options.json';

export interface FinanceAnalyzeSurfaceOptions {
  defaultSymbol: string;
  defaultTimeframe: string;
  supportedSymbols: string[];
  supportedTimeframes: string[];
  labels: {
    query: string;
    symbol: string;
    timeframe: string;
  };
  copy: {
    queryPlaceholder: string;
    analyzePlaceholder: string;
    dashboardHint: string;
    analyzeHint: string;
  };
}

export function getFinanceAnalyzeSurfaceOptions(): FinanceAnalyzeSurfaceOptions {
  return {
    defaultSymbol: surfaceOptions.defaultSymbol,
    defaultTimeframe: surfaceOptions.defaultTimeframe,
    supportedSymbols: [...surfaceOptions.supportedSymbols],
    supportedTimeframes: [...surfaceOptions.supportedTimeframes],
    labels: { ...surfaceOptions.labels },
    copy: { ...surfaceOptions.copy },
  };
}
