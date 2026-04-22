export type WorkspaceTabType = 'review_detail' | 'recommendation_detail' | 'trace_detail';

export interface WorkspaceTab {
  id: string;
  type: WorkspaceTabType;
  title: string;
  refId: string;
}
