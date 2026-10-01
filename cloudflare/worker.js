/**
 * zorVPN — Cloudflare Worker Subscription Reverse Proxy & Cache
 * 
 * Features:
 * - Unblocks raw.githubusercontent.com in Mainland China via Cloudflare Global Edge
 * - Multi-Tier Support:
 *   - iOS Shadowrocket Lite (Top 30 nodes, instant load) -> /lite or /ZorVPN-lite.txt
 *   - iOS Shadowrocket Standard (Top 60 curated nodes) -> /ZorVPN.txt or /shadowrocket
 *   - Clash / FlClash / Stash (Inline rules, 100% verified) -> /ZorVPN.yaml or /clash
 *   - Full Pool Base64 -> /all or /ZorVPN-all.txt
 *   - Raw Plaintext URIs -> /nodes or /ZorVPN-nodes.txt
 * - Auto-detects client User-Agent:
 *   - Shadowrocket -> serves Base64 automatically (no JSON errors!)
 *   - Clash / FlClash / Stash -> serves Clash YAML automatically
 * - Edge Caching (300 seconds) to prevent GitHub rate-limiting
 * - Injects standard subscription headers:
 *   - profile-update-interval: 6 (auto-update every 6 hours)
 *   - subscription-userinfo: quota progress display
 */

const RAW_BASE = "https://raw.githubusercontent.com/hamzawih0/zorVPN/main";
const CACHE_TTL = 300; // 5 minutes

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const userAgent = (request.headers.get("User-Agent") || "").toLowerCase();
    const pathname = url.pathname.toLowerCase();

    const isShadowrocket = userAgent.includes("shadowrocket");
    const isClash = userAgent.includes("clash") || userAgent.includes("stash") || userAgent.includes("meta");

    // Home info route (Only for regular web browsers, NOT proxy clients)
    if ((pathname === "/" || pathname === "") && !isShadowrocket && !isClash) {
      return new Response(
        JSON.stringify({
          status: "online",
          service: "zorVPN Cloudflare Edge Subscription Proxy",
          subscriptions: {
            ios_shadowrocket_lite_recommended: `${url.origin}/ZorVPN-lite.txt`,
            ios_shadowrocket_standard: `${url.origin}/ZorVPN.txt`,
            clash_flclash_stash_yaml: `${url.origin}/ZorVPN.yaml`,
            all_nodes_base64: `${url.origin}/ZorVPN-all.txt`,
            raw_uri_nodes: `${url.origin}/ZorVPN-nodes.txt`
          },
          quick_guide: {
            ios_shadowrocket: "Add as Type: Subscribe using /ZorVPN-lite.txt (Top 30) or /ZorVPN.txt (Top 60)",
            clash_flclash: "Add as URL subscription using /ZorVPN.yaml"
          },
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

    // Determine target subscription file
    let targetFilename = "ZorVPN.yaml";
    let contentType = "text/yaml; charset=utf-8";

    if (pathname.includes("lite")) {
      targetFilename = "ZorVPN-lite.txt";
      contentType = "text/plain; charset=utf-8";
    } else if (pathname.includes("all")) {
      targetFilename = "ZorVPN-all.txt";
      contentType = "text/plain; charset=utf-8";
    } else if (pathname.includes("nodes")) {
      targetFilename = "ZorVPN-nodes.txt";
      contentType = "text/plain; charset=utf-8";
    } else if (pathname.includes("yaml") || pathname.includes("yml") || pathname.includes("clash")) {
      targetFilename = "ZorVPN.yaml";
      contentType = "text/yaml; charset=utf-8";
    } else if (pathname.includes("txt") || pathname.includes("shadowrocket") || isShadowrocket) {
      targetFilename = "ZorVPN.txt";
      contentType = "text/plain; charset=utf-8";
    }

    const upstreamUrl = `${RAW_BASE}/${targetFilename}`;
    const cache = caches.default;
    let response = await cache.match(request);

    if (!response) {
      const fetchHeaders = new Headers();
      fetchHeaders.set("User-Agent", request.headers.get("User-Agent") || "ClashVerge/1.0");

      const upstreamResponse = await fetch(upstreamUrl, {
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
      headers.set("content-type", contentType);
      headers.set("content-disposition", `inline; filename="${targetFilename}"`);
      headers.set("profile-update-interval", "6");
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
};
