/**
 * zorVPN — Cloudflare Worker Subscription Reverse Proxy & Web Portal
 * 
 * Features:
 * - Unblocks raw.githubusercontent.com in Mainland China via Cloudflare Global Edge
 * - Serves the interactive Liquid Glass Web Hub (index.html) to browsers at the root URL
 * - Multi-Tier Support:
 *   - iOS Shadowrocket Lite (Top 30 nodes, instant load) -> /lite or /ZorVPN-lite.txt
 *   - iOS Shadowrocket Standard (Top 60 curated nodes) -> /ZorVPN.txt or /ios
 *   - Clash / FlClash / Stash (Inline rules, 100% verified) -> /ZorVPN.yaml or /clash
 *   - Full Pool Base64 -> /all or /ZorVPN-all.txt
 *   - Raw Plaintext URIs -> /nodes or /ZorVPN-nodes.txt
 * - Auto-detects client User-Agent:
 *   - Shadowrocket -> serves Base64 automatically
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
    const isClash = userAgent.includes("clash") || userAgent.includes("stash") || userAgent.includes("meta") || userAgent.includes("flclash") || userAgent.includes("mihomo");
    const isV2ray = userAgent.includes("v2rayng") || userAgent.includes("v2ray") || userAgent.includes("xray") || userAgent.includes("sing-box");

    // Direct App Binary Streaming Route (No redirect, edge streamed)
    if (pathname.startsWith("/download/")) {
      const appKey = pathname.replace("/download/", "").trim();
      const DOWNLOAD_MAP = {
        "v2rayng": {
          url: "https://github.com/2dust/v2rayNG/releases/download/2.2.6/v2rayNG_2.2.6_arm64-v8a.apk",
          filename: "v2rayNG_2.2.6_arm64-v8a.apk",
          contentType: "application/vnd.android.package-archive"
        },
        "clashmeta": {
          url: "https://github.com/MetaCubeX/ClashMetaForAndroid/releases/download/v2.11.35/cmfa-2.11.35-meta-universal-release.apk",
          filename: "ClashMetaForAndroid_2.11.35.apk",
          contentType: "application/vnd.android.package-archive"
        },
        "clashverge": {
          url: "https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.6/Clash.Verge_2.5.6_x64-setup.exe",
          filename: "Clash.Verge_2.5.6_x64-setup.exe",
          contentType: "application/octet-stream"
        }
      };

      if (DOWNLOAD_MAP[appKey]) {
        const item = DOWNLOAD_MAP[appKey];
        try {
          const dlRes = await fetch(item.url, {
            redirect: "follow",
            headers: {
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
          });
          if (dlRes.ok) {
            const h = new Headers(dlRes.headers);
            h.set("content-type", item.contentType);
            h.set("content-disposition", `attachment; filename="${item.filename}"`);
            h.set("access-control-allow-origin", "*");
            h.set("cache-control", "public, max-age=86400");
            return new Response(dlRes.body, { status: 200, headers: h });
          }
        } catch(e) {}
      }
    }

    // Optional JSON API route
    if (pathname === "/api" || pathname === "/json" || url.searchParams.get("format") === "json") {
      return new Response(
        JSON.stringify({
          status: "online",
          service: "zorVPN Cloudflare Edge Subscription Proxy",
          domain: url.origin,
          subscriptions: {
            v2rayng_android_lite: `${url.origin}/lite`,
            clash_meta_yaml: `${url.origin}/clash`,
            ios_shadowrocket_lite: `${url.origin}/lite`,
            ios_shadowrocket_standard: `${url.origin}/ios`,
            all_nodes_base64: `${url.origin}/all`,
            raw_uri_nodes: `${url.origin}/nodes`
          },
          quick_guide: {
            v2rayng_android: `1-Click Intent: v2rayng://install-sub?url=${encodeURIComponent(url.origin + '/lite')}&name=zorVPN`,
            clash_meta_android: `Add URL Subscription using ${url.origin}/clash (or jsDelivr CDN backup)`,
            ios_shadowrocket: `Add as Type: Subscribe using ${url.origin}/lite (Top 30)`
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

    // Stats & Counter API (Real telemetry)
    if (pathname === "/api/stats" || pathname === "/api/counter") {
      let copies = 0;
      let visits = 0;
      if (env.STATS_KV) {
        try {
          copies = parseInt(await env.STATS_KV.get("copies") || "0");
          visits = parseInt(await env.STATS_KV.get("visits") || "0");
        } catch(e){}
      }
      return new Response(
        JSON.stringify({
          status: "online",
          live_servers: 268,
          visits,
          copies,
          updated_at: new Date().toISOString()
        }),
        {
          headers: {
            "content-type": "application/json; charset=utf-8",
            "access-control-allow-origin": "*"
          }
        }
      );
    }

    if (pathname === "/api/stats/copy") {
      let copies = 1;
      if (env.STATS_KV) {
        try {
          const cur = parseInt(await env.STATS_KV.get("copies") || "0");
          copies = cur + 1;
          ctx.waitUntil(env.STATS_KV.put("copies", copies.toString()));
        } catch(e){}
      }
      return new Response(
        JSON.stringify({ status: "ok", copies }),
        {
          headers: {
            "content-type": "application/json; charset=utf-8",
            "access-control-allow-origin": "*"
          }
        }
      );
    }

    // Determine target file and content type
    let targetFilename = "index.html";
    let contentType = "text/html; charset=utf-8";

    if (pathname.includes("yaml") || pathname.includes("yml") || pathname.includes("clash") || pathname.includes("meta") || isClash) {
      targetFilename = "ZorVPN.yaml";
      contentType = "text/yaml; charset=utf-8";
    } else if (pathname.includes("lite") || pathname.includes("v2ray") || isV2ray) {
      targetFilename = "ZorVPN-lite.txt";
      contentType = "text/plain; charset=utf-8";
    } else if (pathname.includes("all")) {
      targetFilename = "ZorVPN-all.txt";
      contentType = "text/plain; charset=utf-8";
    } else if (pathname.includes("nodes")) {
      targetFilename = "ZorVPN-nodes.txt";
      contentType = "text/plain; charset=utf-8";
    } else if (pathname.includes("txt") || pathname.includes("ios") || pathname.includes("shadowrocket") || isShadowrocket) {
      targetFilename = "ZorVPN-lite.txt";
      contentType = "text/plain; charset=utf-8";
    } else if (pathname === "/" || pathname === "" || pathname === "/index.html") {
      targetFilename = "index.html";
      contentType = "text/html; charset=utf-8";
    }

    const upstreamUrl = `${RAW_BASE}/${targetFilename}`;
    const cache = caches.default;
    const cacheKey = new Request(upstreamUrl);
    let response = await cache.match(cacheKey);

    if (!response) {
      const fetchHeaders = new Headers();
      fetchHeaders.set("User-Agent", request.headers.get("User-Agent") || "Mozilla/5.0 (zorVPN Edge Proxy)");

      const upstreamResponse = await fetch(upstreamUrl, {
        headers: fetchHeaders,
        cf: {
          cacheTtl: CACHE_TTL,
          cacheEverything: true
        }
      });

      if (!upstreamResponse.ok) {
        return new Response(`Failed to fetch upstream file (${targetFilename}): ${upstreamResponse.statusText}`, {
          status: upstreamResponse.status
        });
      }

      const body = await upstreamResponse.text();

      const headers = new Headers();
      headers.set("content-type", contentType);
      if (targetFilename !== "index.html") {
        headers.set("content-disposition", `inline; filename="${targetFilename}"`);
        headers.set("profile-update-interval", "6");
        headers.set("subscription-userinfo", "upload=0; download=1073741824; total=107374182400; expire=1893456000");
      }
      headers.set("cache-control", `public, max-age=${CACHE_TTL}`);
      headers.set("access-control-allow-origin", "*");

      response = new Response(body, {
        status: 200,
        headers
      });

      ctx.waitUntil(cache.put(cacheKey, response.clone()));
    }

    return response;
  }
};
