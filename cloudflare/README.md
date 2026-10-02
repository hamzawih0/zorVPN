# ☁️ Deploying zorVPN on Cloudflare (Free `.dev` Short Domain)

Deploying zorVPN to Cloudflare gives you a **free, short `.dev` domain** (`.workers.dev` or `.pages.dev`) that is hosted on Cloudflare's 330+ global edge locations and is **unblocked in Mainland China**.

It serves:
- 🌐 **Interactive Web Hub** (`index.html`) when opened by any web browser at `https://zorvpn.<subdomain>.workers.dev/`
- 🍏 **iOS Shadowrocket Lite (Top 30 Nodes)** at `/lite` or `/ZorVPN-lite.txt` (or automatically when User-Agent is Shadowrocket)
- ⚡ **iOS Shadowrocket Standard (Top 60 Nodes)** at `/ios` or `/ZorVPN.txt`
- 🎯 **Clash / FlClash YAML** at `/clash` or `/ZorVPN.yaml` (or automatically when User-Agent is Clash)
- 🌐 **Full Verified Pool (200+ Nodes)** at `/all` or `/ZorVPN-all.txt`

---

## 🚀 Option 1: Cloudflare Workers (Free `.workers.dev` Domain) — Recommended

This method takes **less than 60 seconds** and requires no command line:

1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. In the left navigation, click **Workers & Pages** → **Create application** → **Create Worker**.
3. Name your worker: `zorvpn`
   *(This gives you `https://zorvpn.<your-subdomain>.workers.dev`)*.
4. Click **Deploy**.
5. On the success screen, click **Edit code**.
6. Open [`cloudflare/worker.js`](worker.js), copy the entire code, and paste it into the Cloudflare code editor (replacing all default code).
7. Click **Deploy** in the top right.

🎉 **Done!** Your service is now live at:
```
https://zorvpn.<your-subdomain>.workers.dev/
```

### Direct Subscription Endpoints on your Worker:
| Platform | Target Endpoint | What It Returns |
| :--- | :--- | :--- |
| **Web Browser** | `https://zorvpn.<subdomain>.workers.dev/` | Interactive Liquid Glass Web Hub with 1-click copy & QR |
| **iOS Shadowrocket Lite** | `https://zorvpn.<subdomain>.workers.dev/lite` | Base64 Top 30 Green Nodes (0.05s load, zero lag) |
| **iOS Shadowrocket Standard**| `https://zorvpn.<subdomain>.workers.dev/ios` | Base64 Top 60 Curated Nodes |
| **Clash / FlClash / Stash** | `https://zorvpn.<subdomain>.workers.dev/clash` | Clash/Mihomo YAML with inline rules & auto fastest |
| **Full Pool** | `https://zorvpn.<subdomain>.workers.dev/all` | Complete archive of all 200+ verified nodes |

---

## ⚡ Option 2: Cloudflare Pages (Free `.pages.dev` Domain)

Cloudflare Pages connects directly to your GitHub repository and automatically re-deploys every time GitHub Actions updates the proxy nodes:

1. In Cloudflare Dashboard, go to **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Select your repository: `hamzawih0/zorVPN`.
3. Set the build configuration:
   - **Project Name**: `zorvpn` *(gives you `https://zorvpn.pages.dev`)*
   - **Framework preset**: None
   - **Build command**: *(leave completely blank)*
   - **Build output directory**: `/`
4. Click **Save and Deploy**.

Cloudflare will deploy your site in ~10 seconds. You can now use:
- Web Portal: `https://zorvpn.pages.dev/`
- iOS Lite: `https://zorvpn.pages.dev/ZorVPN-lite.txt`
- Clash: `https://zorvpn.pages.dev/ZorVPN.yaml`

---

## 🔄 Option 3: Automated Deploy via GitHub Actions

Our repository's GitHub Actions workflow [`.github/workflows/update.yml`](../.github/workflows/update.yml) has built-in support for automatic Cloudflare deployment:

1. In Cloudflare Dashboard, go to **My Profile** → **API Tokens** → **Create Token** → use the **Edit Cloudflare Workers** template.
2. Copy the generated API Token.
3. In your GitHub repository (`hamzawih0/zorVPN`), go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
4. Name: `CLOUDFLARE_API_TOKEN`
5. Value: *(paste your API token)*

Every 6 hours when GitHub Actions runs the active delay verification, it will automatically deploy the fresh nodes and worker code to Cloudflare without you having to lift a finger!
