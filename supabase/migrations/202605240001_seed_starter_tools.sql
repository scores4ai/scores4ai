insert into public.tools (
  id, slug, name, provider, category, description, website_url, pricing_type, source_status, metadata
)
values
  ('11111111-1111-4111-8111-111111111111','chatgpt','ChatGPT','OpenAI','LLM','General-purpose AI assistant for writing, analysis, and coding.','https://chatgpt.com','Paid','live',
   '{"logo":"🤖","benchmark_score":95,"community_score":94,"programmer_score":96,"pricing":{"plan":"Plus/Team/Enterprise","notes":"Subscription and API pricing available"}}'::jsonb),
  ('22222222-2222-4222-8222-222222222222','claude','Claude','Anthropic','LLM','Reasoning-focused assistant with strong long-context performance.','https://claude.ai','Paid','live',
   '{"logo":"🧭","benchmark_score":94,"community_score":93,"programmer_score":95,"pricing":{"plan":"Pro/Team/Enterprise","notes":"Subscription and API pricing available"}}'::jsonb),
  ('33333333-3333-4333-8333-333333333333','gemini','Gemini','Google','LLM','Multimodal model family for research, coding, and productivity.','https://gemini.google.com','Freemium','live',
   '{"logo":"✨","benchmark_score":92,"community_score":90,"programmer_score":91,"pricing":{"plan":"Free + paid tiers","notes":"API and app plans vary by model"}}'::jsonb),
  ('44444444-4444-4444-8444-444444444444','grok','Grok','xAI','LLM','Conversational and reasoning model integrated across xAI products.','https://grok.com','Paid','live',
   '{"logo":"⚡","benchmark_score":89,"community_score":88,"programmer_score":87,"pricing":{"plan":"Premium tiers","notes":"Pricing varies by access tier"}}'::jsonb),
  ('55555555-5555-4555-8555-555555555555','perplexity','Perplexity','Perplexity','Research','Answer engine with web-grounded citations and fast retrieval.','https://www.perplexity.ai','Freemium','live',
   '{"logo":"🔎","benchmark_score":90,"community_score":91,"programmer_score":88,"pricing":{"plan":"Free + Pro","notes":"Pro plan unlocks higher limits and models"}}'::jsonb),
  ('66666666-6666-4666-8666-666666666666','cursor','Cursor','Anysphere','Coding Tool','AI-native code editor focused on repo-aware coding workflows.','https://cursor.com','Paid','live',
   '{"logo":"⌨️","benchmark_score":91,"community_score":92,"programmer_score":95,"pricing":{"plan":"Pro/Business","notes":"Seat-based pricing"}}'::jsonb),
  ('77777777-7777-4777-8777-777777777777','windsurf','Windsurf','Codeium','Coding Tool','AI development environment with autonomous coding assistance.','https://windsurf.com','Freemium','live',
   '{"logo":"🌊","benchmark_score":88,"community_score":89,"programmer_score":90,"pricing":{"plan":"Free + paid tiers","notes":"Usage and seat-based options"}}'::jsonb),
  ('88888888-8888-4888-8888-888888888888','midjourney','Midjourney','Midjourney','Image','Text-to-image generation platform for high-quality visual design.','https://www.midjourney.com','Paid','live',
   '{"logo":"🎨","benchmark_score":93,"community_score":94,"programmer_score":86,"pricing":{"plan":"Subscription tiers","notes":"Monthly plans by generation limits"}}'::jsonb),
  ('99999999-9999-4999-8999-999999999999','runway','Runway','Runway','Video','Video generation and editing platform for creative production workflows.','https://runwayml.com','Freemium','live',
   '{"logo":"🎬","benchmark_score":90,"community_score":89,"programmer_score":85,"pricing":{"plan":"Free + paid tiers","notes":"Credit-based and subscription options"}}'::jsonb)
on conflict (slug) do update
set
  name = excluded.name,
  provider = excluded.provider,
  category = excluded.category,
  description = excluded.description,
  website_url = excluded.website_url,
  pricing_type = excluded.pricing_type,
  source_status = excluded.source_status,
  metadata = excluded.metadata,
  updated_at = now();
