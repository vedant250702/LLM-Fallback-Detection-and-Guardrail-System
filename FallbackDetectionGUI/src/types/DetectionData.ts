export interface DetectionData{
  query: string;
  response: string;
  retrieved_context: string | string[];
  fallback_label: 0 | 1;
  confidence: number;
  reason: string;
  similarity_scores: Record<string, number>;
}

export interface MessageType{
  message:string
}