insert into public.ai_tools (slug,name,category,description,website_url,overall_score)
values
('chatgpt','ChatGPT','General LLM','General-purpose AI assistant for writing, coding, and analysis.','https://chatgpt.com',95),
('claude','Claude','General LLM','Reasoning-focused assistant with strong long-context quality.','https://claude.ai',94),
('gemini','Gemini','General LLM','Multimodal AI assistant for productivity and research workflows.','https://gemini.google.com',92),
('grok','Grok','General LLM','Conversational model ecosystem designed for real-time interactions.','https://grok.com',89),
('perplexity','Perplexity','Research & Search','Answer engine optimized for web-grounded research with citations.','https://www.perplexity.ai',90),
('cursor','Cursor','Coding Assistant','AI-native code editor with repo-aware coding support.','https://cursor.com',93),
('windsurf','Windsurf','Coding Assistant','AI development environment for accelerated coding workflows.','https://windsurf.com',88),
('midjourney','Midjourney','Image Generation','High-quality image generation platform for creative teams.','https://www.midjourney.com',93),
('runway','Runway','Video Generation','AI video generation and editing suite for production teams.','https://runwayml.com',90),
('github-copilot','GitHub Copilot','Coding Assistant','Code completion and pair-programming assistant integrated with IDEs.','https://github.com/features/copilot',91),
('notion-ai','Notion AI','Productivity','AI workspace assistant for docs, summaries, and writing tasks.','https://www.notion.so/product/ai',87),
('jasper','Jasper','Marketing & Writing','Content generation platform for marketing teams and brand workflows.','https://www.jasper.ai',85),
('canva-ai','Canva AI','Design & UI','Design suite with integrated AI generation and editing tools.','https://www.canva.com',86),
('elevenlabs','ElevenLabs','Voice & Audio','AI voice generation and speech tools for media production.','https://elevenlabs.io',89),
('suno','Suno','Voice & Audio','Music generation platform for rapid audio ideation.','https://suno.com',84),
('stability-ai','Stability AI','Image Generation','Open model ecosystem for image generation and creative tooling.','https://stability.ai',83),
('hugging-face','Hugging Face','AI Infrastructure','Model hub and tooling ecosystem for AI development and deployment.','https://huggingface.co',90),
('openrouter','OpenRouter','AI Infrastructure','Unified API layer for accessing multiple AI model providers.','https://openrouter.ai',88)
on conflict (slug) do update
set name = excluded.name,
    category = excluded.category,
    description = excluded.description,
    website_url = excluded.website_url,
    overall_score = excluded.overall_score;
