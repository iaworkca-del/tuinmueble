---
name: Gemini free-tier image quota
description: Free Gemini API keys often have a hard 0 request/day quota for image-generation ("Nano Banana") models, even though text models work fine.
---

Free-tier `GEMINI_API_KEY` values can return `429 RESOURCE_EXHAUSTED` for
image-capable models (e.g. `gemini-2.5-flash-image`) with a quota limit of 0,
while text-only models (e.g. `gemini-2.5-flash`) work normally on the same key.

**Why:** Google's free tier does not always include image generation access;
this surfaces only at call time, not at key-creation time, so it's easy to
assume image generation will "just work" once text generation does.

**How to apply:** Always generate text and image in separate try/except blocks
so an image failure never blocks the text content from being produced/saved.
Design any content pipeline (news, listings, etc.) to persist successfully
without an image and show a graceful fallback (placeholder icon/last-known
image) in the UI. If a user reports images never generating, check for this
quota error before assuming a code bug — the fix is upgrading/enabling billing
on the Gemini API key, not code changes.
