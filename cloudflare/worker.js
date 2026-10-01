/**
 * zorVPN — Cloudflare Worker Subscription Reverse Proxy & Cache
 * 
 * Features:
 * - Unblocks raw.githubusercontent.com in Mainland China via Cloudflare Global Edge
 * - Edge Caching (300 seconds) to prevent GitHub rate-limiting
 * - Injects standard Clash/Stash/Shadowrocket subscription headers:
 *   - profile-update-interval: 6 (auto-update every 6 hours)
 *   - content-disposition: inline; filename="ZorVPN.yaml"
 *   - subscription-userinfo: quota progress display
 */

const GITHUB_RAW_URL = "https://raw.githubusercontent.com/hamzawih0/zorVPN/main/ZorVPN.yaml";
const CACHE_TTL = 300; // 5 minutes

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Health check or home route
    if (url.pathname === "/" || url.pathname === "") {
      return new Response(
        JSON.stringify({
          status: "online",
          service: "zorVPN Cloudflare Edge Subscription Proxy",
          subscription_url: `${url.origin}/ZorVPN.yaml`,
          upstream: GITHUB_RAW_URL,
          updated_at: new Date().toISOString()
        }, null, 2),
        {
          headers: {
            "content-type": "application/json; charset=utf-8",
            "access-control-allow-origin": "*"
          }
        }
      );
    }

    // Serve ZorVPN.yaml (or clash.yaml)
    if (url.pathname.toLowerCase().endsWith(".yaml") || url.pathname.toLowerCase().endsWith(".yml") || url.pathname === "/sub") {
      const cache = caches.default;
      let response = await cache.match(request);

      if (!response) {
        const fetchHeaders = new Headers();
        fetchHeaders.set("User-Agent", request.headers.get("User-Agent") || "ClashVerge/1.0");

        const upstreamResponse = await fetch(GITHUB_RAW_URL, {
          headers: fetchHeaders,
          cf: {
            cacheTtl: CACHE_TTL,
            cacheEverything: true
          }
        });

        if (!upstreamResponse.ok) {
          return new Response(`Failed to fetch upstream subscription: ${upstreamResponse.statusText}`, {
            status: upstreamResponse.status
          });
        }

        const body = await upstreamResponse.text();

        const headers = new Headers();
        headers.set("content-type", "text/yaml; charset=utf-8");
        headers.set("content-disposition", 'inline; filename="ZorVPN.yaml"');
        headers.set("profile-update-interval", "6");
        // Simulated clean 100GB traffic display in Clash/Stash/FlClash UI
        headers.set("subscription-userinfo", "upload=0; download=1073741824; total=107374182400; expire=1893456000");
        headers.set("cache-control", `public, max-age=${CACHE_TTL}`);
        headers.set("access-control-allow-origin", "*");

        response = new Response(body, {
          status: 200,
          headers
        });

        ctx.waitUntil(cache.put(request, response.clone()));
      }

      return response;
    }

    return new Response("Not Found", { status: 404 });
  }
};
