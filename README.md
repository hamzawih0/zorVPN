# zorVPN — Free Multi-Platform VPN Subscription

![Nodes](https://img.shields.io/badge/Nodes-2700+-blue?style=for-the-badge)
![Countries](https://img.shields.io/badge/Countries-40+-success?style=for-the-badge)
![Auto-Update](https://img.shields.io/badge/Update-Every%206h-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

A high-performance, free Clash/Mihomo YAML subscription with **2,700+ active proxy nodes** across **40+ countries**, auto-aggregated from top-tier GitHub sources with health checks, deduplication, and automated updates via GitHub Actions.

## ⚡ Subscription URLs

Because `raw.githubusercontent.com` is blocked by the Great Firewall (GFW) in Mainland China, testers without a proxy should use the **China Accelerated Link** or **Global CDN Link** below:

### 🇨🇳 Direct China Links (No Proxy Needed — Fixes `EOF` Error)

| Mirror Provider | Subscription URL |
|:----------------|:-----------------|
| ⚡ **GHProxy (Recommended)** | `https://ghproxy.net/https://raw.githubusercontent.com/hamzawih0/zorVPN/main/ZorVPN.yaml` |
| 🚀 **GH-Proxy Mirror** | `https://gh-proxy.com/https://raw.githubusercontent.com/hamzawih0/zorVPN/main/ZorVPN.yaml` |
| 🌐 **jsDelivr Global CDN** | `https://cdn.jsdelivr.net/gh/hamzawih0/zorVPN@main/ZorVPN.yaml` |
| ⚡ **Fastly CDN** | `https://fastly.jsdelivr.net/gh/hamzawih0/zorVPN@main/ZorVPN.yaml` |

> 📱 **For Testers**: Copy the **GHProxy** or **jsDelivr** link above and paste directly into **FlClash**, **Clash Verge Rev**, **Stash**, or **Shadowrocket**. The subscription will automatically import as **`ZorVPN`**!

### 🌍 Global Direct Link (For Users with Existing Proxy or Outside China)
```
https://raw.githubusercontent.com/hamzawih0/zorVPN/main/ZorVPN.yaml
```

---

## ☁️ Cloudflare Pages & Worker (Self-Hosted Edge CDN)

Want your own dedicated subscription domain (e.g. `https://zorvpn.pages.dev/ZorVPN.yaml`) with zero blocking?
Check out the **[Cloudflare Deployment Guide](cloudflare/README.md)** (Supports 1-click Cloudflare Pages & Workers).

## 🎯 Proxy Groups

| Group | Type | Purpose |
|:------|:-----|:--------|
| 🎯 **zorVPN** | `select` | Master selector — pick strategy or country |
| ⚡ **Fastest** | `url-test` | Auto-select lowest latency node (300s test, 50ms tolerance) |
| 🛡️ **Fallback** | `fallback` | Cascading reliability — auto-failover across regions |
| 🤖 **AI Services** | `url-test` | Optimized for ChatGPT, Claude, Gemini, Perplexity, Poe, Suno |
| 🎬 **Streaming** | `url-test` | Optimized for Netflix, YouTube, Spotify, Disney+, Twitch, TikTok |
| 🇺🇸 🇭🇰 🇯🇵 🇸🇬 🇩🇪 ... | `url-test` | 40 country-specific pools |

## 🌍 Countries Available (40+ Regions)

| Region | Countries |
|:-------|:----------|
| **Asia-Pacific** | 🇭🇰 Hong Kong · 🇯🇵 Japan · 🇸🇬 Singapore · 🇰🇷 South Korea · 🇹🇼 Taiwan · 🇮🇳 India · 🇦🇺 Australia · 🇲🇾 Malaysia · 🇹🇭 Thailand · 🇻🇳 Vietnam · 🇵🇭 Philippines · 🇮🇩 Indonesia |
| **North America** | 🇺🇸 United States · 🇨🇦 Canada |
| **Europe** | 🇩🇪 Germany · 🇬🇧 United Kingdom · 🇫🇷 France · 🇳🇱 Netherlands · 🇸🇪 Sweden · 🇨🇿 Czech Republic · 🇮🇹 Italy · 🇪🇸 Spain · 🇷🇴 Romania · 🇪🇪 Estonia · 🇱🇻 Latvia · 🇵🇱 Poland · 🇦🇹 Austria · 🇨🇭 Switzerland · 🇫🇮 Finland · 🇳🇴 Norway · 🇩🇰 Denmark · 🇮🇪 Ireland · 🇺🇦 Ukraine |
| **Middle East & Eurasia** | 🇷🇺 Russia · 🇹🇷 Turkey · 🇮🇱 Israel · 🇦🇪 UAE |
| **South America & Africa** | 🇧🇷 Brazil · 🇨🇱 Chile · 🇿🇦 South Africa |

## 📱 Supported Clients

| Platform | Client | Support |
|:---------|:-------|:--------|
| **Windows** | Clash Verge Rev | ✅ Full |
| **macOS** | Clash Verge Rev / ClashX Meta | ✅ Full |
| **iOS** | Stash (recommended) / Shadowrocket | ✅ Full |
| **Android** | FlClash / ClashMeta for Android | ✅ Full |
| **Linux** | Mihomo CLI | ✅ Full |
| **iOS** | Surge / Quantumult X | ⚠️ Use subconverter |

## 🚀 Setup Instructions

### Desktop (Windows / macOS / Linux)

1. Download or clone this repo
2. Open **Clash Verge Rev** → Profiles → Import Local File
3. Select `clash.yaml` → Activate
4. To enable TUN mode (system-wide proxy), use a Merge profile:
   ```yaml
   tun:
     enable: true
   ```

### iOS — Stash (Recommended)

1. Open Stash → Settings → Subscribe
2. Add new → paste the raw GitHub URL
3. Tap to update and activate

### iOS — Shadowrocket

1. Tap **+** → Type: Subscribe
2. Paste the raw GitHub URL → Save
3. Select the config and connect

### Android — FlClash

1. Profiles → Add → URL
2. Paste the raw GitHub URL → Save → Activate

### Surge / Quantumult X

Use a subconverter to transform the Clash YAML:
```
# Surge
https://api.subconverter.xyz/sub?target=surge&ver=4&url=YOUR_ENCODED_URL

# Quantumult X
https://api.subconverter.xyz/sub?target=quanx&url=YOUR_ENCODED_URL
```

## 🔗 Node Sources
zorVPN continuously aggregates and validates nodes from 6 major auto-updating sources:

| Source | Update Frequency | Nodes Contributed | Method |
|:-------|:----------------|:------------------|:-------|
| [anaer/Sub](https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml) | Every few hours | ~1,600+ | Large multi-airport merge |
| [ermaozi/get_subscribe](https://github.com/ermaozi/get_subscribe) | Hourly | ~500+ | Speed-tested, latency verified |
| [sinspired/airport](https://github.com/sinspired/airport) | Daily | ~550+ | Strict deduplication & test |
| [peasoft/NoMoreWalls](https://github.com/peasoft/NoMoreWalls) | Daily | ~400+ | Filtered high-speed nodes |
| [awesome-vpn/awesome-vpn](https://github.com/awesome-vpn/awesome-vpn) | Daily | ~40+ | Direct proxy harvest |
| [sunmiao4458/free-proxy-airport](https://github.com/sunmiao4458/free-proxy-airport) | Every 30 min | ~35+ | Health checks & low latency |

## 📐 Routing Rules

| Category | Action | Rule Source |
|:---------|:-------|:-----------|
| **AI** (ChatGPT, Claude, Gemini, etc.) | → 🤖 AI Services | Inline DOMAIN-SUFFIX |
| **Streaming** (Netflix, YouTube, etc.) | → 🎬 Streaming | Inline DOMAIN-SUFFIX |
| **Ads** | → REJECT | ACL4SSR BanAD + BanProgramAD |
| **Telegram** | → 🎯 zorVPN | ACL4SSR Telegram |
| **Social** (Twitter, Discord, Reddit) | → 🎯 zorVPN | Inline DOMAIN-SUFFIX |
| **Dev Tools** (GitHub, Docker, npm) | → 🎯 zorVPN | Inline DOMAIN-SUFFIX |
| **Google** | → 🎯 zorVPN | Inline + ACL4SSR |
| **Apple** | → DIRECT | ACL4SSR Apple |
| **China** | → DIRECT | ACL4SSR ChinaDomain + GEOIP |
| **Everything else** | → 🎯 zorVPN | MATCH catch-all |

## ⚠️ Disclaimer

- **Free nodes are public** — do NOT use for banking, passwords, or sensitive data
- **Nodes go stale** — refresh the subscription regularly for best results
- **For educational use only** — comply with your local laws and regulations
- **No warranty** — provided as-is, no guarantees of availability or speed

## 📄 License

MIT — Free to use, modify, and distribute.

---

**zorVPN** — Built with 🔥 by Zero
