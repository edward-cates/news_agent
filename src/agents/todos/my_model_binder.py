from lasagna import known_models, partial_bind_model

# https://github.com/ollama/ollama
BIND_OLLAMA_phi4_mini = partial_bind_model('ollama', 'phi4-mini')
BIND_OLLAMA_deepseek_r1_7b = partial_bind_model('ollama', 'deepseek-r1')

BIND_OPENAI_o3_mini = partial_bind_model('openai', 'o3-mini-2025-01-31')

def my_model_binder():
    # return known_models.BIND_ANTHROPIC_claude_35_sonnet()
    # return known_models.BIND_OPENAI_gpt_4o()
    return BIND_OPENAI_o3_mini()
