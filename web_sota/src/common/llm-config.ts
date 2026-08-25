const STORAGE_KEY = "fastsearch_llm_config";

export interface LlmConfig {
  provider: string;
  model: string;
  baseUrl: string;
  systemPrompt: string;
}

const DEFAULT_SYSTEM_PROMPT = `You are a FastSearch expert. Help users find files across millions of entries. Suggest patterns (glob, path), content search terms, and follow-up actions. Be concise and actionable.`;

export function getLlmConfig(): LlmConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<LlmConfig>;
      return {
        provider:
          typeof parsed.provider === "string" ? parsed.provider : "ollama",
        model: typeof parsed.model === "string" ? parsed.model : "",
        baseUrl: typeof parsed.baseUrl === "string" ? parsed.baseUrl : "",
        systemPrompt:
          typeof parsed.systemPrompt === "string"
            ? parsed.systemPrompt
            : DEFAULT_SYSTEM_PROMPT,
      };
    }
  } catch {
    // ignore
  }
  return {
    provider: "ollama",
    model: "",
    baseUrl: "",
    systemPrompt: DEFAULT_SYSTEM_PROMPT,
  };
}

export function setLlmConfig(config: Partial<LlmConfig>): void {
  const current = getLlmConfig();
  const next: LlmConfig = {
    provider: config.provider ?? current.provider,
    model: config.model ?? current.model,
    baseUrl: config.baseUrl ?? current.baseUrl,
    systemPrompt: config.systemPrompt ?? current.systemPrompt,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
}
