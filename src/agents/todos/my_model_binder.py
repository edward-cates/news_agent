from lasagna import known_models

def my_model_binder():
    return known_models.BIND_ANTHROPIC_claude_35_sonnet()
    # return known_models.BIND_OPENAI_gpt_4o()
    # return known_models.BIND_OLLAMA_phi4_mini()
