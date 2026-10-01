# Deploying zorVPN Subscription on Cloudflare (Unblocked in China)

Because `raw.githubusercontent.com` is blocked by the Great Firewall (GFW) in Mainland China, testers without a proxy cannot fetch subscriptions directly from GitHub.

Deploying on Cloudflare solves this completely by caching and serving `ZorVPN.yaml` via Cloudflare's global CDN edge.

---

## ⚡ Option 1: Cloudflare Pages (Recommended — Easiest, 0 Code)

Cloudflare Pages automatically syncs with this GitHub repository and serves `ZorVPN.yaml` worldwide.

1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Go to **Compute (Workers & Pages)** → **Create** → **Pages** → **Connect to Git**.
3. Select the repository `hamzawih0/zorVPN`.
4. Set Build Settings:
   - **Framework preset**: None
   - **Build command**: *(leave blank)*
   - **Build output directory**: `/`
5. Click **Save and Deploy**.
6. Cloudflare will give you a free domain: `https://<your-project>.pages.dev`.

Your testers can now subscribe using:
```
https://<your-project>.pages.dev/ZorVPN.yaml
```

---

## 🚀 Option 2: Cloudflare Worker (Custom Headers & Edge Caching)

1. In Cloudflare Dashboard, go to **Workers & Pages** → **Create Application** → **Create Worker**.
2. Name your worker (e.g. `zorvpn-sub`).
3. Click **Deploy**, then click **Edit code**.
4. Replace the entire code with the contents of [`worker.js`](worker.js).
5. Click **Deploy**.
6. *(Optional)* Add a Custom Domain in worker settings (e.g. `sub.yourdomain.com`).

Your testers can now subscribe using:
```
https://zorvpn-sub.<your-subdomain>.workers.dev/ZorVPN.yaml
```

---

## 🛡️ Immediate Accelerator Links (No Cloudflare Setup Needed!)

Testers in China can also immediately use public accelerator mirrors without setting anything up:

| Type | Link |
|:-----|:-----|
| **GHProxy (Recommended)** | `https://ghproxy.net/https://raw.githubusercontent.com/hamzawih0/zorVPN/main/ZorVPN.yaml` |
| **GH-Proxy Mirror** | `https://gh-proxy.com/https://raw.githubusercontent.com/hamzawih0/zorVPN/main/ZorVPN.yaml` |
| **jsDelivr Fastly CDN** | `https://fastly.jsdelivr.net/gh/hamzawih0/zorVPN@main/ZorVPN.yaml` |
| **jsDelivr Global CDN** | `https://cdn.jsdelivr.net/gh/hamzawih0/zorVPN@main/ZorVPN.yaml` |
