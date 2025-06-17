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

      // Transform field names for AI Gateway compatibility
      const transformedConfig = {};
      if (body.generationConfig) {
        // Convert camelCase to snake_case for known problematic fields
        if (body.generationConfig.responseMimeType) {
          transformedConfig.response_mime_type = body.generationConfig.responseMimeType;
        }
        if (body.generationConfig.temperature !== undefined) {
          transformedConfig.temperature = body.generationConfig.temperature;
        }
        if (body.generationConfig.maxOutputTokens) {
          transformedConfig.max_output_tokens = body.generationConfig.maxOutputTokens;
        }
      }

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
          generation_config: transformedConfig,
          // Note: tools might not be supported in v1 endpoint
          // tools: body.tools || []
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