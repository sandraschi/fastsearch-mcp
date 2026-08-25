export interface ToolResult {
  content: Array<{
    type: string;
    text?: string;
    [key: string]: any;
  }>;
  isError?: boolean;
}

class MCPClient {
  private baseUrl: string;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  async listTools() {
    try {
      const response = await fetch(`${this.baseUrl}/tools`);
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("Failed to list tools:", error);
      throw error;
    }
  }

  async callTool(name: string, args: Record<string, any> = {}): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/tools/${name}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ arguments: args }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`,
        );
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error(`Failed to call tool ${name}:`, error);
      throw error;
    }
  }

  async fetchFile(path: string): Promise<{
    path: string;
    type: string;
    mime: string;
    content: string;
    size: number;
    truncated?: boolean;
  }> {
    const response = await fetch(
      `${this.baseUrl}/file?path=${encodeURIComponent(path)}`,
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `HTTP error! status: ${response.status}`,
      );
    }
    return response.json();
  }

  async getLlmModels(
    provider: string,
    baseUrl?: string,
  ): Promise<{
    provider: string;
    base_url: string;
    models: string[];
    error?: string;
  }> {
    const params = new URLSearchParams({ provider });
    if (baseUrl) params.set("base_url", baseUrl);
    const response = await fetch(`${this.baseUrl}/llm/models?${params}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async llmChat(params: {
    messages: Array<{ role: string; content: string }>;
    model?: string;
    provider?: string;
    base_url?: string;
  }): Promise<{ content: string }> {
    const response = await fetch(`${this.baseUrl}/llm/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async llmAnalyze(params: {
    search_results: unknown;
    prompt?: string;
    model?: string;
    provider?: string;
    base_url?: string;
  }): Promise<{ content: string }> {
    const response = await fetch(`${this.baseUrl}/llm/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async llmAnalyzeForensic(params: {
    search_results: unknown;
    model?: string;
    provider?: string;
    base_url?: string;
  }): Promise<{ content: string }> {
    const response = await fetch(`${this.baseUrl}/llm/analyze-forensic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async runTests(params?: {
    pattern?: string;
    directory?: string;
    max_results?: number;
  }): Promise<{
    passed: number;
    total: number;
    results: Array<{
      name: string;
      passed: boolean;
      message: string;
      duration_ms: number;
      details?: unknown;
    }>;
  }> {
    const response = await fetch(`${this.baseUrl}/tests/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params ?? {}),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async searchDirect(params: {
    pattern: string;
    directory?: string;
    max_results?: number;
    pagination_mode?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    success: boolean;
    service_down?: boolean;
    error?: string;
    results?: any[];
    count?: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      return await response.json();
    } catch (error) {
      console.error("searchDirect failed:", error);
      return {
        success: false,
        service_down: true,
        error: String(error),
        results: [],
        count: 0,
      };
    }
  }

  async getServiceStatusDirect(): Promise<{
    success: boolean;
    running?: boolean;
    service_state?: string;
    pipe_connected?: boolean;
    executable_path?: string;
    error?: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/service/status`);
      return await response.json();
    } catch (error) {
      return { success: false, running: false, error: String(error) };
    }
  }

  async startServiceDirect(): Promise<{
    success: boolean;
    message?: string;
    error?: string;
    logs?: string[];
    details?: Record<string, any>;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/service/start`, {
        method: "POST",
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  async getServiceLogsDirect(): Promise<{
    success: boolean;
    logs: string[];
    error?: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/service/logs`);
      return await response.json();
    } catch (error) {
      return { success: false, logs: [], error: String(error) };
    }
  }

  async stopServiceDirect(): Promise<{
    success: boolean;
    message?: string;
    error?: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/service/stop`, {
        method: "POST",
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  async restartServiceDirect(): Promise<{
    success: boolean;
    message?: string;
    error?: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/service/restart`, {
        method: "POST",
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }
}

export const mcpClient = new MCPClient();
