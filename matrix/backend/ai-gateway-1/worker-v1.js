export default {
  async fetch(request, env) {
    // Only allow requests from your domain
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*', // Replace with your domain in production
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Only allow POST requests
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { 
        status: 405,
        headers: corsHeaders 
      });
    }

    try {
      // Get the request body
      const body = await request.json();

      // Build the Google AI Studio URL through AI Gateway
      const GATEWAY_URL = `https://gateway.ai.cloudflare.com/v1/${env.CF_ACCOUNT_ID}/${env.GATEWAY_ID}/google-ai-studio/v1/models/${body.model || 'gemini-2.0-flash'}:generateContent`;

      // Forward the request with the API key
      const response = await fetch(GATEWAY_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': env.GOOGLE_API_KEY, 
        },
        body: JSON.stringify({
          contents: body.contents,
          generationConfig: body.generationConfig,
          tools: body.tools || []
        })
      });

      const data = await response.json();
      
      return new Response(JSON.stringify(data), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  }
};