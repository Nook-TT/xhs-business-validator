# TikHub Xiaohongshu API notes

Use App V2 endpoints. Current parameter names matter; do not reuse old `sort` or `noteType` examples.

## Search notes

`GET https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_notes`

Required or useful parameters:

- `keyword`
- `page`, starting at 1
- `sort_type`: `general`, `time_descending`, `popularity_descending`, `comment_descending`, or `collect_descending`
- `note_type`: `不限`, `视频笔记`, or `普通笔记`
- `time_filter`: `不限`, `一天内`, `一周内`, or `半年内`
- `search_id` and `search_session_id` from page 1 when requesting later pages
- `ai_mode=0`

Notes are normally under `data.data.items[].note`. Normalize IDs, title, description, author, timestamp, and interaction counts. Counts may be strings; accept Arabic numerals and Chinese `万` suffixes.

## Note comments

`GET https://api.tikhub.io/api/v1/xiaohongshu/app_v2/get_note_comments`

Use `note_id`, `cursor`, `index=0`, `pageArea=UNFOLDED`, and `sort_strategy=like_count` for the first evidence pass. Comments are normally under `data.data.comments`; include visible sub-comments but label them separately.

## Billing and cache

Xiaohongshu endpoints have historically cost USD 0.01 per successful request. Treat this as an estimate and report it as such. Successful responses may contain a `cache_url` valid for about 24 hours. The collection script maintains a workspace cache keyed by endpoint and parameters so repeat analysis does not pay again unnecessarily.

## Error handling

- `401`: invalid or expired token; stop.
- `402`: insufficient paid balance or a route that does not accept free credit; show only the sanitized localized message.
- `403`: retry at most once with the browser-like User-Agent already used by the script.
- `429`: stop the run and report rate limiting; do not loop.

Never log request headers. Recursively redact keys or values containing `authorization`, `token`, `secret`, `api_key`, or bearer-token patterns before persisting an error.

