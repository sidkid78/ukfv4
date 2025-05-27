/**
 * Gemini AI API Client Extension
 * Handles all AI-related backend communication
 */

import { 
    AIRequest, 
    AIResponse, 
    AIHealthStatus,
    LayerAIAnalysis,
    AIResearchSynthesis,
    AISafetyAnalysis,
    AIUsageStats,
    AIChatMessage,
    AIQuerySuggestion,
    GeminiModel
  } from '@/types/ai';
  
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  class APIError extends Error {
    constructor(
      message: string,
      public status: number,
      public response?: Record<string, any>
    ) {
      super(message);
      this.name = 'APIError';
    }
  }
  
  async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };
  
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }
  
      return await response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`, 0);
    }
  }
  
  // Gemini AI API
  export const aiAPI = {
    // Health and Status
    async getHealth(): Promise<AIHealthStatus> {
      return apiRequest<AIHealthStatus>('/api/ai/health');
    },
  
    async getUsageStats(): Promise<AIUsageStats> {
      return apiRequest<AIUsageStats>('/api/ai/usage-stats');
    },
  
    async listModels(): Promise<{ models: Array<{ name: string; description: string }> }> {
      return apiRequest('/api/ai/models');
    },
  
    // Direct AI Generation
    async generate(request: AIRequest, sessionId?: string): Promise<AIResponse> {
      const params = new URLSearchParams();
      if (sessionId) {
        params.append('session_id', sessionId);
      }
      
      return aiRequest<AIResponse>(`/api/ai/generate${params.toString() ? `?${params.toString()}` : ''}`, {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },
  
    // Streaming AI Generation
    async generateStream(
      request: AIRequest, 
      sessionId?: string,
      onChunk?: (chunk: string) => void
    ): Promise<ReadableStreamDefaultReader<Uint8Array>> {
      const params = new URLSearchParams();
      if (sessionId) {
        params.append('session_id', sessionId);
      }
  
      const response = await fetch(`${API_BASE}/api/ai/generate${params.toString() ? `?${params.toString()}` : ''}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...request, stream: true }),
      });
  
      if (!response.ok) {
        throw new APIError(`Stream request failed: ${response.statusText}`, response.status);
      }
  
      const reader = response.body?.getReader();
      if (!reader) {
        throw new APIError('No stream reader available', 500);
      }
  
      // Process stream chunks
      if (onChunk) {
        const decoder = new TextDecoder();
        let buffer = '';
  
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
  
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (line.trim()) {
              onChunk(line);
            }
          }
        }
  
        if (buffer.trim()) {
          onChunk(buffer);
        }
      }
  
      return reader;
    },
  
    // Layer-specific AI Analysis
    async analyzeQuery(
      query: string, 
      context?: Record<string, any>, 
      sessionId?: string
    ): Promise<{
      query: string;
      analysis: string;
      confidence: number;
      processing_time: number;
      model_used: string;
    }> {
      const params = new URLSearchParams();
      if (sessionId) {
        params.append('session_id', sessionId);
      }
  
      return apiRequest(`/api/ai/analyze-query${params.toString() ? `?${params.toString()}` : ''}`, {
        method: 'POST',
        body: JSON.stringify({ query, context }),
      });
    },
  
    // Research Generation
    async generateResearch(
      topic: string,
      persona: string = 'domain_expert',
      context?: Record<string, any>,
      sessionId?: string
    ): Promise<{
      topic: string;
      persona: string;
      research: string;
      confidence: number;
      processing_time: number;
      model_used: string;
    }> {
      const params = new URLSearchParams();
      if (sessionId) {
        params.append('session_id', sessionId);
      }
  
      return apiRequest(`/api/ai/research${params.toString() ? `?${params.toString()}` : ''}`, {
        method: 'POST',
        body: JSON.stringify({ topic, persona, context }),
      });
    },
  
    // Confidence Evaluation
    async evaluateConfidence(
      content: string,
      criteria: string[],
      sessionId?: string
    ): Promise<{
      content_length: number;
      criteria_count: number;
      evaluation: string;
      confidence: number;
      processing_time: number;
    }> {
      const params = new URLSearchParams();
      if (sessionId) {
        params.append('session_id', sessionId);
      }
  
      return apiRequest(`/api/ai/evaluate-confidence${params.toString() ? `?${params.toString()}` : ''}`, {
        method: 'POST',
        body: JSON.stringify({ content, criteria }),
      });
    },
  
    // Safety Analysis
    async checkSafety(
      content: string,
      context?: Record<string, any>,
      layer: number = 0
    ): Promise<AISafetyAnalysis> {
      return apiRequest<AISafetyAnalysis>('/api/ai/safety-check', {
        method: 'POST',
        body: JSON.stringify({ content, context, layer }),
      });
    },
  };
  
  // Chat-specific API for direct AI interaction
  export const aiChatAPI = {
    async sendMessage(
      message: string,
      sessionId: string,
      model: GeminiModel = 'gemini-2.0-flash',
      systemPrompt?: string
    ): Promise<AIChatMessage> {
      const request: AIRequest = {
        prompt: message,
        model,
        system_prompt: systemPrompt,
        temperature: 0.7,
      };
  
      const response = await aiAPI.generate(request, sessionId);
      
      return {
        id: response.request_id,
        role: 'assistant',
        content: response.content,
        timestamp: response.timestamp,
        model: response.model as GeminiModel,
        confidence: response.confidence,
        processing_time: response.processing_time,
        metadata: {
          usage: response.usage,
          reasoning_trace: response.reasoning_trace,
        },
      };
    },
  
    async streamMessage(
      message: string,
      sessionId: string,
      model: GeminiModel = 'gemini-2.0-flash',
      onChunk: (chunk: string) => void,
      systemPrompt?: string
    ): Promise<void> {
      const request: AIRequest = {
        prompt: message,
        model,
        system_prompt: systemPrompt,
        temperature: 0.7,
        stream: true,
      };
  
      await aiAPI.generateStream(request, sessionId, onChunk);
    },
  };
  
  // Query Suggestions API
  export const aiSuggestionsAPI = {
    async getQuerySuggestions(
      category?: string,
      complexity?: 'low' | 'medium' | 'high'
    ): Promise<AIQuerySuggestion[]> {
      // This would be implemented if you add a suggestions endpoint
      // For now, return mock suggestions based on category
      const mockSuggestions: AIQuerySuggestion[] = [
        {
          id: '1',
          query: 'Analyze the safety implications of autonomous vehicles in urban environments',
          category: 'safety_analysis',
          complexity: 0.8,
          estimated_layers: [1, 2, 3, 4, 5],
          description: 'Multi-faceted analysis of autonomous vehicle safety with expert perspectives',
          tags: ['safety', 'transportation', 'AI ethics', 'urban planning'],
        },
        {
          id: '2',
          query: 'What are the potential benefits and risks of AI in healthcare diagnostics?',
          category: 'analysis',
          complexity: 0.7,
          estimated_layers: [1, 2, 3, 4],
          description: 'Balanced analysis of AI applications in medical diagnostics',
          tags: ['healthcare', 'AI', 'diagnostics', 'medical ethics'],
        },
        {
          id: '3',
          query: 'How might climate change affect global food security over the next 20 years?',
          category: 'prediction',
          complexity: 0.9,
          estimated_layers: [1, 2, 3, 4, 5, 6],
          description: 'Complex predictive analysis requiring multiple expert perspectives',
          tags: ['climate change', 'food security', 'prediction', 'global trends'],
        },
      ];
  
      // Filter by category and complexity if specified
      return mockSuggestions.filter(suggestion => {
        if (category && suggestion.category !== category) return false;
        if (complexity) {
          const complexityMap = { low: 0.3, medium: 0.6, high: 0.9 };
          if (Math.abs(suggestion.complexity - complexityMap[complexity]) > 0.2) return false;
        }
        return true;
      });
    },
  
    async generateSuggestion(
      userInput: string,
      context?: Record<string, any>
    ): Promise<AIQuerySuggestion> {
      // This would use AI to generate a suggestion based on user input
      // For now, return a mock suggestion
      return {
        id: Date.now().toString(),
        query: `Analyze and evaluate: ${userInput}`,
        category: 'analysis',
        complexity: 0.6,
        estimated_layers: [1, 2, 3],
        description: `AI-generated analysis query based on your input: "${userInput}"`,
        tags: ['ai-generated', 'analysis'],
      };
    },
  };
  
  export default {
    aiAPI,
    aiChatAPI,
    aiSuggestionsAPI,
  };
  