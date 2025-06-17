echo "$GOOGLE_API_KEY" | wrangler secret put GOOGLE_API_KEY

wrangler deploy --var CF_ACCOUNT_ID:$CLOUDFLARE_ACCOUNT_ID