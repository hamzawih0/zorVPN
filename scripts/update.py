"""
zorVPN — Subscription Generator & Updater
Fetches nodes from verified, auto-updating GitHub repositories,
deduplicates, normalizes, detects country geolocation, groups intelligently,
and outputs a production-ready, cross-platform Clash / Mihomo configuration.
"""

import sys
import os
import re
import ssl
import json
import socket
import hashlib
import urllib.request
from datetime import datetime, timezone
from collections import defaultdict
import yaml

# Path to output
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_YAML = os.path.join(ROOT_DIR, "clash.yaml")

# Verified upstream subscription sources
SOURCES = [
    {
        "name": "ermaozi/get_subscribe",
        "url": "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
        "type": "clash",
    },
    {
        "name": "anaer/Sub",
        "url": "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
        "type": "clash",
    },
    {
        "name": "sinspired/airport",
        "url": "https://raw.githubusercontent.com/sinspired/airport/main/subs/clashfree.yaml",
        "type": "clash",
    },
    {
        "name": "peasoft/NoMoreWalls",
        "url": "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.meta.yml",
        "type": "clash",
    },
    {
        "name": "awesome-vpn/awesome-vpn",
        "url": "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/clash.yaml",
        "type": "clash",
    },
    {
        "name": "sunmiao4458/free-proxy-airport",
        "url": "https://sunmiao4458.github.io/free-proxy-airport/clash.yaml",
        "type": "clash",
    },
]

# Country detection lookup table: (Flag, ISO Code, Display Name)
COUNTRY_MAP = {
    # Asia-Pacific
    'HK': ('🇭🇰', 'HK', 'Hong Kong'), 'hongkong': ('🇭🇰', 'HK', 'Hong Kong'), '香港': ('🇭🇰', 'HK', 'Hong Kong'), 'HKG': ('🇭🇰', 'HK', 'Hong Kong'),
    'JP': ('🇯🇵', 'JP', 'Japan'), 'japan': ('🇯🇵', 'JP', 'Japan'), '日本': ('🇯🇵', 'JP', 'Japan'), 'JPN': ('🇯🇵', 'JP', 'Japan'), 'tokyo': ('🇯🇵', 'JP', 'Japan'), 'osaka': ('🇯🇵', 'JP', 'Japan'),
    'SG': ('🇸🇬', 'SG', 'Singapore'), 'singapore': ('🇸🇬', 'SG', 'Singapore'), '新加坡': ('🇸🇬', 'SG', 'Singapore'), 'SGP': ('🇸🇬', 'SG', 'Singapore'), '狮城': ('🇸🇬', 'SG', 'Singapore'),
    'KR': ('🇰🇷', 'KR', 'South Korea'), 'korea': ('🇰🇷', 'KR', 'South Korea'), '韩国': ('🇰🇷', 'KR', 'South Korea'), 'KOR': ('🇰🇷', 'KR', 'South Korea'), 'seoul': ('🇰🇷', 'KR', 'South Korea'),
    'TW': ('🇹🇼', 'TW', 'Taiwan'), 'taiwan': ('🇹🇼', 'TW', 'Taiwan'), '台湾': ('🇹🇼', 'TW', 'Taiwan'), 'TWN': ('🇹🇼', 'TW', 'Taiwan'), 'taipei': ('🇹🇼', 'TW', 'Taiwan'),
    'IN': ('🇮🇳', 'IN', 'India'), 'india': ('🇮🇳', 'IN', 'India'), '印度': ('🇮🇳', 'IN', 'India'), 'mumbai': ('🇮🇳', 'IN', 'India'),
    'AU': ('🇦🇺', 'AU', 'Australia'), 'australia': ('🇦🇺', 'AU', 'Australia'), '澳大利亚': ('🇦🇺', 'AU', 'Australia'), 'sydney': ('🇦🇺', 'AU', 'Australia'), 'melbourne': ('🇦🇺', 'AU', 'Australia'),
    'MY': ('🇲🇾', 'MY', 'Malaysia'), 'malaysia': ('🇲🇾', 'MY', 'Malaysia'), '马来西亚': ('🇲🇾', 'MY', 'Malaysia'),
    'TH': ('🇹🇭', 'TH', 'Thailand'), 'thailand': ('🇹🇭', 'TH', 'Thailand'), '泰国': ('🇹🇭', 'TH', 'Thailand'),
    'VN': ('🇻🇳', 'VN', 'Vietnam'), 'vietnam': ('🇻🇳', 'VN', 'Vietnam'), '越南': ('🇻🇳', 'VN', 'Vietnam'),
    'PH': ('🇵🇭', 'PH', 'Philippines'), 'philippines': ('🇵🇭', 'PH', 'Philippines'), '菲律宾': ('🇵🇭', 'PH', 'Philippines'),
    'ID': ('🇮🇩', 'ID', 'Indonesia'), 'indonesia': ('🇮🇩', 'ID', 'Indonesia'), '印尼': ('🇮🇩', 'ID', 'Indonesia'),

    # North America
    'US': ('🇺🇸', 'US', 'United States'), 'united states': ('🇺🇸', 'US', 'United States'), '美国': ('🇺🇸', 'US', 'United States'), 'USA': ('🇺🇸', 'US', 'United States'), 'america': ('🇺🇸', 'US', 'United States'),
    'CA': ('🇨🇦', 'CA', 'Canada'), 'canada': ('🇨🇦', 'CA', 'Canada'), '加拿大': ('🇨🇦', 'CA', 'Canada'), 'CAN': ('🇨🇦', 'CA', 'Canada'),

    # Europe
    'DE': ('🇩🇪', 'DE', 'Germany'), 'germany': ('🇩🇪', 'DE', 'Germany'), '德国': ('🇩🇪', 'DE', 'Germany'), 'DEU': ('🇩🇪', 'DE', 'Germany'), 'frankfurt': ('🇩🇪', 'DE', 'Germany'),
    'GB': ('🇬🇧', 'GB', 'United Kingdom'), 'uk': ('🇬🇧', 'GB', 'United Kingdom'), 'united kingdom': ('🇬🇧', 'GB', 'United Kingdom'), '英国': ('🇬🇧', 'GB', 'United Kingdom'), 'GBR': ('🇬🇧', 'GB', 'United Kingdom'), 'london': ('🇬🇧', 'GB', 'United Kingdom'),
    'FR': ('🇫🇷', 'FR', 'France'), 'france': ('🇫🇷', 'FR', 'France'), '法国': ('🇫🇷', 'FR', 'France'), 'FRA': ('🇫🇷', 'FR', 'France'), 'paris': ('🇫🇷', 'FR', 'France'),
    'NL': ('🇳🇱', 'NL', 'Netherlands'), 'netherlands': ('🇳🇱', 'NL', 'Netherlands'), '荷兰': ('🇳🇱', 'NL', 'Netherlands'), 'amsterdam': ('🇳🇱', 'NL', 'Netherlands'), 'NLD': ('🇳🇱', 'NL', 'Netherlands'),
    'SE': ('🇸🇪', 'SE', 'Sweden'), 'sweden': ('🇸🇪', 'SE', 'Sweden'), '瑞典': ('🇸🇪', 'SE', 'Sweden'), 'SWE': ('🇸🇪', 'SE', 'Sweden'),
    'IT': ('🇮🇹', 'IT', 'Italy'), 'italy': ('🇮🇹', 'IT', 'Italy'), '意大利': ('🇮🇹', 'IT', 'Italy'), 'ITA': ('🇮🇹', 'IT', 'Italy'), 'milan': ('🇮🇹', 'IT', 'Italy'), 'rome': ('🇮🇹', 'IT', 'Italy'),
    'ES': ('🇪🇸', 'ES', 'Spain'), 'spain': ('🇪🇸', 'ES', 'Spain'), '西班牙': ('🇪🇸', 'ES', 'Spain'), 'ESP': ('🇪🇸', 'ES', 'Spain'), 'madrid': ('🇪🇸', 'ES', 'Spain'),
    'CZ': ('🇨🇿', 'CZ', 'Czech Republic'), 'czech': ('🇨🇿', 'CZ', 'Czech Republic'), '捷克': ('🇨🇿', 'CZ', 'Czech Republic'), 'CZE': ('🇨🇿', 'CZ', 'Czech Republic'),
    'PL': ('🇵🇱', 'PL', 'Poland'), 'poland': ('🇵🇱', 'PL', 'Poland'), '波兰': ('🇵🇱', 'PL', 'Poland'), 'POL': ('🇵🇱', 'PL', 'Poland'), 'warsaw': ('🇵🇱', 'PL', 'Poland'),
    'RO': ('🇷🇴', 'RO', 'Romania'), 'romania': ('🇷🇴', 'RO', 'Romania'), '罗马尼亚': ('🇷🇴', 'RO', 'Romania'), 'ROU': ('🇷🇴', 'RO', 'Romania'),
    'EE': ('🇪🇪', 'EE', 'Estonia'), 'estonia': ('🇪🇪', 'EE', 'Estonia'), '爱沙尼亚': ('🇪🇪', 'EE', 'Estonia'), 'EST': ('🇪🇪', 'EE', 'Estonia'),
    'LV': ('🇱🇻', 'LV', 'Latvia'), 'latvia': ('🇱🇻', 'LV', 'Latvia'), '拉脱维亚': ('🇱🇻', 'LV', 'Latvia'), 'LVA': ('🇱🇻', 'LV', 'Latvia'),
    'LT': ('🇱🇹', 'LT', 'Lithuania'), 'lithuania': ('🇱🇹', 'LT', 'Lithuania'), '立陶宛': ('🇱🇹', 'LT', 'Lithuania'),
    'AT': ('🇦🇹', 'AT', 'Austria'), 'austria': ('🇦🇹', 'AT', 'Austria'), '奥地利': ('🇦🇹', 'AT', 'Austria'), 'AUT': ('🇦🇹', 'AT', 'Austria'), 'vienna': ('🇦🇹', 'AT', 'Austria'),
    'CH': ('🇨🇭', 'CH', 'Switzerland'), 'switzerland': ('🇨🇭', 'CH', 'Switzerland'), '瑞士': ('🇨🇭', 'CH', 'Switzerland'), 'CHE': ('🇨🇭', 'CH', 'Switzerland'), 'zurich': ('🇨🇭', 'CH', 'Switzerland'),
    'PT': ('🇵🇹', 'PT', 'Portugal'), 'portugal': ('🇵🇹', 'PT', 'Portugal'), '葡萄牙': ('🇵🇹', 'PT', 'Portugal'),
    'HR': ('🇭🇷', 'HR', 'Croatia'), 'croatia': ('🇭🇷', 'HR', 'Croatia'), '克罗地亚': ('🇭🇷', 'HR', 'Croatia'),
    'FI': ('🇫🇮', 'FI', 'Finland'), 'finland': ('🇫🇮', 'FI', 'Finland'), '芬兰': ('🇫🇮', 'FI', 'Finland'), 'FIN': ('🇫🇮', 'FI', 'Finland'),
    'NO': ('🇳🇴', 'NO', 'Norway'), 'norway': ('🇳🇴', 'NO', 'Norway'), '挪威': ('🇳🇴', 'NO', 'Norway'),
    'DK': ('🇩🇰', 'DK', 'Denmark'), 'denmark': ('🇩🇰', 'DK', 'Denmark'), '丹麦': ('🇩🇰', 'DK', 'Denmark'),
    'IE': ('🇮🇪', 'IE', 'Ireland'), 'ireland': ('🇮🇪', 'IE', 'Ireland'), '爱尔兰': ('🇮🇪', 'IE', 'Ireland'),
    'UA': ('🇺🇦', 'UA', 'Ukraine'), 'ukraine': ('🇺🇦', 'UA', 'Ukraine'), '乌克兰': ('🇺🇦', 'UA', 'Ukraine'),

    # Middle East & Eurasia
    'RU': ('🇷🇺', 'RU', 'Russia'), 'russia': ('🇷🇺', 'RU', 'Russia'), '俄罗斯': ('🇷🇺', 'RU', 'Russia'), 'RUS': ('🇷🇺', 'RU', 'Russia'), 'moscow': ('🇷🇺', 'RU', 'Russia'),
    'TR': ('🇹🇷', 'TR', 'Turkey'), 'turkey': ('🇹🇷', 'TR', 'Turkey'), '土耳其': ('🇹🇷', 'TR', 'Turkey'), 'TUR': ('🇹🇷', 'TR', 'Turkey'), 'istanbul': ('🇹🇷', 'TR', 'Turkey'),
    'IL': ('🇮🇱', 'IL', 'Israel'), 'israel': ('🇮🇱', 'IL', 'Israel'), '以色列': ('🇮🇱', 'IL', 'Israel'),
    'IR': ('🇮🇷', 'IR', 'Iran'), 'iran': ('🇮🇷', 'IR', 'Iran'), '伊朗': ('🇮🇷', 'IR', 'Iran'),
    'AE': ('🇦🇪', 'AE', 'United Arab Emirates'), 'uae': ('🇦🇪', 'AE', 'United Arab Emirates'), 'dubai': ('🇦🇪', 'AE', 'United Arab Emirates'), '阿联酋': ('🇦🇪', 'AE', 'United Arab Emirates'),

    # South America & Africa
    'BR': ('🇧🇷', 'BR', 'Brazil'), 'brazil': ('🇧🇷', 'BR', 'Brazil'), '巴西': ('🇧🇷', 'BR', 'Brazil'),
    'CL': ('🇨🇱', 'CL', 'Chile'), 'chile': ('🇨🇱', 'CL', 'Chile'), '智利': ('🇨🇱', 'CL', 'Chile'),
    'AR': ('🇦🇷', 'AR', 'Argentina'), 'argentina': ('🇦🇷', 'AR', 'Argentina'), '阿根廷': ('🇦🇷', 'AR', 'Argentina'),
    'ZA': ('🇿🇦', 'ZA', 'South Africa'), 'south africa': ('🇿🇦', 'ZA', 'South Africa'), '南非': ('🇿🇦', 'ZA', 'South Africa'),
}

EMOJI_FLAG_MAP = {
    '🇭🇰': 'HK', '🇯🇵': 'JP', '🇸🇬': 'SG', '🇺🇸': 'US', '🇩🇪': 'DE',
    '🇬🇧': 'GB', '🇫🇷': 'FR', '🇳🇱': 'NL', '🇸🇪': 'SE', '🇮🇹': 'IT',
    '🇪🇸': 'ES', '🇨🇿': 'CZ', '🇷🇺': 'RU', '🇹🇷': 'TR', '🇮🇱': 'IL',
    '🇨🇱': 'CL', '🇪🇪': 'EE', '🇱🇻': 'LV', '🇨🇦': 'CA', '🇰🇷': 'KR',
    '🇹🇼': 'TW', '🇵🇱': 'PL', '🇷🇴': 'RO', '🇦🇹': 'AT', '🇨🇭': 'CH',
    '🇮🇳': 'IN', '🇧🇷': 'BR', '🇦🇺': 'AU', '🇫🇮': 'FI', '🇵🇹': 'PT',
    '🇭🇷': 'HR', '🇮🇷': 'IR', '🇲🇾': 'MY', '🇹🇭': 'TH', '🇻🇳': 'VN',
    '🇵🇭': 'PH', '🇮🇩': 'ID', '🇳🇴': 'NO', '🇩🇰': 'DK', '🇮🇪': 'IE',
    '🇦🇪': 'AE', '🇦🇷': 'AR', '🇿🇦': 'ZA', '🇺🇦': 'UA',
}

def detect_country(name: str, server: str = "") -> str:
    """Detect country ISO 2-letter code from proxy name and server address."""
    if not name:
        name = ""
    
    # 1. Flag emoji check
    for emoji, code in EMOJI_FLAG_MAP.items():
        if emoji in name:
            return code
    
    # 2. Keyword match (longest match first)
    name_lower = name.lower()
    sorted_keywords = sorted(COUNTRY_MAP.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        kw_lower = kw.lower()
        # Word boundary or direct substring for non-ASCII
        if any(ord(c) > 127 for c in kw):
            if kw in name:
                _, code, _ = COUNTRY_MAP[kw]
                return code
        else:
            pattern = r'(?:\b|_|-)' + re.escape(kw_lower) + r'(?:\b|_|-|\d)'
            if re.search(pattern, name_lower) or kw_lower in name_lower:
                _, code, _ = COUNTRY_MAP[kw]
                return code

    # 3. Server domain TLD fallback (e.g. server.de, proxy.sg, hk-vless.xyz)
    if server:
        srv_lower = server.lower()
        parts = srv_lower.split('.')
        if len(parts) >= 2:
            tld = parts[-1].upper()
            if tld in EMOJI_FLAG_MAP.values():
                return tld
        for code in ['hk', 'jp', 'sg', 'us', 'de', 'uk', 'fr', 'kr', 'tw']:
            if f"-{code}-" in srv_lower or f"_{code}_" in srv_lower or f".{code}." in srv_lower:
                return code.upper()

    return 'XX'


def proxy_fingerprint(proxy: dict) -> str:
    """Unique hash fingerprint of node to eliminate duplicates across providers."""
    server = str(proxy.get('server', '')).strip().lower()
    port = str(proxy.get('port', '')).strip()
    ptype = str(proxy.get('type', '')).strip().lower()
    cred = str(proxy.get('uuid', proxy.get('password', ''))).strip()
    return hashlib.sha256(f"{server}:{port}:{ptype}:{cred}".encode('utf-8')).hexdigest()


def fetch_url(url: str, timeout: int = 15) -> bytes:
    """Fetch URL with custom User-Agent and SSL context."""
    headers = {
        'User-Agent': 'ClashforWindows/0.20.39 ClashX/1.118.0 Stash/2.6.0',
        'Accept': '*/*',
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
        return response.read()


def parse_clash_yaml(content_bytes: bytes) -> list:
    """Parse Clash YAML content and return list of proxy dicts."""
    try:
        text = content_bytes.decode('utf-8', errors='ignore')
        # Skip markdown wrappers if any
        if '```yaml' in text:
            text = text.split('```yaml', 1)[1].split('```', 1)[0]
        elif '```' in text:
            text = text.split('```', 1)[1].split('```', 1)[0]

        data = yaml.safe_load(text)
        if isinstance(data, dict) and 'proxies' in data and isinstance(data['proxies'], list):
            return [p for p in data['proxies'] if isinstance(p, dict) and 'server' in p and 'port' in p]
    except Exception as e:
        print(f"    [Error parsing YAML]: {e}")
    return []


def build_zorvpn():
    print("═" * 70)
    print("  🚀 zorVPN Subscription Updater — Aggregating High-Speed Nodes")
    print("═" * 70)

    all_proxies = []
    seen_fingerprints = set()

    for src in SOURCES:
        name = src['name']
        url = src['url']
        print(f"  ➜ Fetching {name} ...", end="", flush=True)
        try:
            data = fetch_url(url, timeout=18)
            proxies = parse_clash_yaml(data)
            added = 0
            for p in proxies:
                fp = proxy_fingerprint(p)
                if fp not in seen_fingerprints:
                    # Clean unwanted tags
                    p_copy = dict(p)
                    seen_fingerprints.add(fp)
                    all_proxies.append(p_copy)
                    added += 1
            print(f"  ✓ {len(proxies)} nodes ({added} unique)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print(f"\n  Total unique valid nodes collected: {len(all_proxies)}")
    if not all_proxies:
        print("  ❌ No proxies collected! Aborting update to protect existing clash.yaml.")
        return False

    # Group by country
    country_groups = defaultdict(list)
    for p in all_proxies:
        original_name = str(p.get('name', ''))
        server = str(p.get('server', ''))
        code = detect_country(original_name, server)
        country_groups[code].append(p)

    print(f"  Detected countries: {len(country_groups)}")
    for code, group in sorted(country_groups.items(), key=lambda x: -len(x[1])):
        if code in EMOJI_FLAG_MAP.values():
            flag = [k for k, v in EMOJI_FLAG_MAP.items() if v == code][0]
            cname = [v[2] for k, v in COUNTRY_MAP.items() if v[1] == code][0]
        else:
            flag, cname = '🌍', 'Other' if code == 'XX' else code
        print(f"    {flag} {cname:<18}: {len(group):>3} nodes")

    # Rename nodes cleanly: Flag + Country + #Idx + Protocol
    renamed_proxies = []
    country_counters = defaultdict(int)

    for p in all_proxies:
        original_name = str(p.get('name', ''))
        server = str(p.get('server', ''))
        code = detect_country(original_name, server)

        if code in EMOJI_FLAG_MAP.values():
            flag = [k for k, v in EMOJI_FLAG_MAP.items() if v == code][0]
            cname = [v[2] for k, v in COUNTRY_MAP.items() if v[1] == code][0]
        else:
            flag, cname = '🌍', 'Other'

        country_counters[cname] += 1
        ptype = str(p.get('type', 'proxy')).upper()
        if ptype == 'HYSTERIA2': ptype = 'Hy2'
        elif ptype == 'VMESS': ptype = 'VMess'
        elif ptype == 'TROJAN': ptype = 'Trojan'
        elif ptype == 'SHADOWSOCKS': ptype = 'SS'

        new_name = f"{flag} {cname} #{country_counters[cname]:02d} {ptype}"
        p['name'] = new_name
        renamed_proxies.append(p)

    all_proxy_names = [p['name'] for p in renamed_proxies]

    # Build Country Pools
    region_pools = {}
    REGION_ORDER = [
        'United States', 'Hong Kong', 'Japan', 'Singapore', 'Germany',
        'United Kingdom', 'France', 'Netherlands', 'South Korea', 'Taiwan',
        'Canada', 'Australia', 'Russia', 'Sweden', 'Czech Republic', 'Italy',
        'Spain', 'Turkey', 'Estonia', 'Latvia', 'India', 'Poland', 'Romania',
        'Brazil', 'Chile', 'Israel', 'Austria', 'Switzerland', 'Finland',
        'Portugal', 'Norway', 'Denmark', 'Ireland', 'Malaysia', 'Thailand',
        'Vietnam', 'Philippines', 'Indonesia', 'United Arab Emirates', 'Ukraine',
        'Other'
    ]

    for country in REGION_ORDER:
        members = [p['name'] for p in renamed_proxies if f" {country} #" in p['name']]
        if members:
            # Find flag
            flag = members[0].split()[0]
            pool_name = f"{flag} {country}"
            region_pools[pool_name] = members

    # AI pool: US, SG, JP, KR, GB, DE, CA, AU
    ai_countries = ['United States', 'Singapore', 'Japan', 'South Korea', 'United Kingdom', 'Germany', 'Canada', 'Australia']
    ai_members = [p['name'] for p in renamed_proxies if any(f" {c} #" in p['name'] for c in ai_countries)]

    # Streaming pool: US, JP, HK, SG, KR, TW, GB
    stream_countries = ['United States', 'Japan', 'Hong Kong', 'Singapore', 'South Korea', 'Taiwan', 'United Kingdom']
    stream_members = [p['name'] for p in renamed_proxies if any(f" {c} #" in p['name'] for c in stream_countries)]

    # ── Proxy Groups ─────────────────────────────────────────────────────────
    proxy_groups = []

    # 1. Master selector (🎯 zorVPN)
    master_options = ["⚡ Fastest", "🛡️ Fallback", "🤖 AI Services", "🎬 Streaming"]
    master_options.extend(list(region_pools.keys()))
    master_options.append("DIRECT")

    proxy_groups.append({
        'name': '🎯 zorVPN',
        'type': 'select',
        'proxies': master_options,
    })

    # 2. Fastest (auto-speedtest all nodes)
    proxy_groups.append({
        'name': '⚡ Fastest',
        'type': 'url-test',
        'proxies': all_proxy_names[:],
        'url': 'http://www.gstatic.com/generate_204',
        'interval': 300,
        'tolerance': 50,
    })

    # 3. Fallback
    fallback_candidates = ["⚡ Fastest"] + list(region_pools.keys())[:8]
    proxy_groups.append({
        'name': '🛡️ Fallback',
        'type': 'fallback',
        'proxies': fallback_candidates,
        'url': 'http://www.gstatic.com/generate_204',
        'interval': 300,
    })

    # 4. AI Services Pool
    if ai_members:
        proxy_groups.append({
            'name': '🤖 AI Services',
            'type': 'url-test',
            'proxies': ai_members,
            'url': 'http://www.gstatic.com/generate_204',
            'interval': 300,
            'tolerance': 100,
        })

    # 5. Streaming Pool
    if stream_members:
        proxy_groups.append({
            'name': '🎬 Streaming',
            'type': 'url-test',
            'proxies': stream_members,
            'url': 'http://www.gstatic.com/generate_204',
            'interval': 300,
            'tolerance': 100,
        })

    # 6. Country Pools
    for pool_name, members in region_pools.items():
        proxy_groups.append({
            'name': pool_name,
            'type': 'url-test',
            'proxies': members,
            'url': 'http://www.gstatic.com/generate_204',
            'interval': 300,
        })

    # ── Configuration Header ────────────────────────────────────────────────
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    header = f"""# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          zorVPN — Premium Subscription                     ║
# ║  Auto-generated: {now_str:<32}                      ║
# ║  Nodes: {len(renamed_proxies):>4} | Countries: {len(region_pools):>2} | Sources: {len(SOURCES):>2}                               ║
# ║  Compatible: Clash Verge Rev, ClashX, Stash, Shadowrocket, FlClash, Surge  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ──────────────────────────────── General Settings ────────────────────────────
mixed-port: 7890
port: 7891
socks-port: 7892
allow-lan: true
mode: rule
log-level: info
ipv6: true
external-controller: 127.0.0.1:9090

# ──────────────────────────── Performance Tuning ─────────────────────────────
unified-delay: true
tcp-concurrent: true
global-client-fingerprint: chrome
find-process-mode: strict

# ────────────────────────────── Geodata Config ───────────────────────────────
geodata-mode: true
geo-auto-update: true
geo-update-interval: 24
geox-url:
  geoip: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip-lite.dat"
  geosite: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat"
  mmdb: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country-lite.mmdb"
  asn: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/GeoLite2-ASN.mmdb"

# ──────────────────────────── Profile Persistence ────────────────────────────
profile:
  store-selected: true
  store-fake-ip: true

# ─────────────────────────── Domain Sniffer (SNI) ────────────────────────────
sniffer:
  enable: true
  parse-pure-ip: true
  override-destination: true
  sniff:
    HTTP:
      ports: [80, 8080-8880]
      override-destination: true
    TLS:
      ports: [443, 8443]
    QUIC:
      ports: [443, 8443]
  skip-domain:
    - "Mijia Cloud"
    - "dlg.io.mi.com"
    - "+.apple.com"

# ──────────────────────────────── TUN Mode ───────────────────────────────────
# Managed by OS or App on iOS / Android / macOS / Windows
tun:
  enable: false
  stack: mixed
  dns-hijack:
    - any:53
    - tcp://any:53
  auto-route: true
  auto-detect-interface: true
  mtu: 1400

# ─────────────────────────────── DNS Config ──────────────────────────────────
dns:
  enable: true
  ipv6: true
  prefer-h3: true
  listen: 0.0.0.0:53
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  fake-ip-filter:
    - "*.lan"
    - "*.local"
    - "cable.auth.com"
    - "router.asus.com"
    - "+.msftconnecttest.com"
    - "+.msftncsi.com"
    - "+.apple.com"
    - "+.icloud.com"
    - "captive.apple.com"
    - "connectivitycheck.gstatic.com"
    - "network-test.debian.org"
    - "detectportal.firefox.com"
    - "+.srv.nintendo.net"
    - "+.stun.playstation.net"
    - "xbox.*.microsoft.com"
    - "+.xboxlive.com"
    - "stun.*"
    - "global.turn.twilio.com"
    - "global.stun.twilio.com"
    - "localhost.*.qq.com"
    - "+.logon.battlenet.com.cn"
    - "+.logon.battle.net"
    - "+.cmpassport.com"
    - "+.pingan.com.cn"
    - "+.cmbchina.com"
    - "pool.ntp.org"
    - "+.pool.ntp.org"
    - "ntp.*.com"
    - "time.*.com"
    - "time.*.apple.com"
  default-nameserver:
    - 223.5.5.5
    - 119.29.29.29
  nameserver:
    - https://doh.pub/dns-query
    - https://dns.alidns.com/dns-query
  fallback:
    - https://1.1.1.1/dns-query
    - https://8.8.8.8/dns-query
    - https://208.67.222.222/dns-query
    - https://9.9.9.9/dns-query
  fallback-filter:
    geoip: true
    geoip-code: CN
    geosite:
      - gfw
    ipcidr:
      - 240.0.0.0/4
      - 0.0.0.0/32
    domain:
      - "+.google.com"
      - "+.github.com"
      - "+.facebook.com"
      - "+.twitter.com"
      - "+.youtube.com"
      - "+.googleapis.com"
"""

    yaml_proxies = yaml.dump({'proxies': renamed_proxies}, allow_unicode=True, default_flow_style=False, sort_keys=False, width=300)
    yaml_groups = yaml.dump({'proxy-groups': proxy_groups}, allow_unicode=True, default_flow_style=False, sort_keys=False, width=300)

    rules_section = """
# ══════════════════════════════════════════════════════════════════════════════
#                         RULE PROVIDERS (ACL4SSR)
# ══════════════════════════════════════════════════════════════════════════════

rule-providers:
  LocalAreaNetwork:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/LocalAreaNetwork.list"
    path: ./ruleset/LocalAreaNetwork.yaml
    interval: 86400
  BanAD:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanAD.list"
    path: ./ruleset/BanAD.yaml
    interval: 86400
  BanProgramAD:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanProgramAD.list"
    path: ./ruleset/BanProgramAD.yaml
    interval: 86400
  GoogleCN:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/GoogleCN.list"
    path: ./ruleset/GoogleCN.yaml
    interval: 86400
  Apple:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Apple.list"
    path: ./ruleset/Apple.yaml
    interval: 86400
  Telegram:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Telegram.list"
    path: ./ruleset/Telegram.yaml
    interval: 86400
  ProxyLite:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyLite.list"
    path: ./ruleset/ProxyLite.yaml
    interval: 86400
  ChinaDomain:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaDomain.list"
    path: ./ruleset/ChinaDomain.yaml
    interval: 86400

# ══════════════════════════════════════════════════════════════════════════════
#                              ROUTING RULES
# ══════════════════════════════════════════════════════════════════════════════

rules:
  # ── Local Area Network ────────────────────────────────────────────────────
  - RULE-SET,LocalAreaNetwork,DIRECT

  # ── Block Advertising ─────────────────────────────────────────────────────
  - RULE-SET,BanAD,REJECT
  - RULE-SET,BanProgramAD,REJECT

  # ── AI Services → AI Pool ─────────────────────────────────────────────────
  - DOMAIN-SUFFIX,openai.com,🤖 AI Services
  - DOMAIN-SUFFIX,chatgpt.com,🤖 AI Services
  - DOMAIN-SUFFIX,ai.com,🤖 AI Services
  - DOMAIN-SUFFIX,claude.ai,🤖 AI Services
  - DOMAIN-SUFFIX,anthropic.com,🤖 AI Services
  - DOMAIN-SUFFIX,gemini.google.com,🤖 AI Services
  - DOMAIN-SUFFIX,bard.google.com,🤖 AI Services
  - DOMAIN-SUFFIX,perplexity.ai,🤖 AI Services
  - DOMAIN-SUFFIX,poe.com,🤖 AI Services
  - DOMAIN-SUFFIX,cohere.com,🤖 AI Services
  - DOMAIN-SUFFIX,huggingface.co,🤖 AI Services
  - DOMAIN-SUFFIX,midjourney.com,🤖 AI Services
  - DOMAIN-SUFFIX,suno.ai,🤖 AI Services
  - DOMAIN-SUFFIX,deepseek.com,🤖 AI Services
  - DOMAIN-SUFFIX,x.ai,🤖 AI Services
  - DOMAIN-SUFFIX,grok.com,🤖 AI Services

  # ── Streaming → Media Pool ────────────────────────────────────────────────
  - DOMAIN-SUFFIX,netflix.com,🎬 Streaming
  - DOMAIN-SUFFIX,nflxvideo.net,🎬 Streaming
  - DOMAIN-SUFFIX,youtube.com,🎬 Streaming
  - DOMAIN-SUFFIX,googlevideo.com,🎬 Streaming
  - DOMAIN-SUFFIX,ytimg.com,🎬 Streaming
  - DOMAIN-SUFFIX,spotify.com,🎬 Streaming
  - DOMAIN-SUFFIX,twitch.tv,🎬 Streaming
  - DOMAIN-SUFFIX,disneyplus.com,🎬 Streaming
  - DOMAIN-SUFFIX,hbomax.com,🎬 Streaming
  - DOMAIN-SUFFIX,hulu.com,🎬 Streaming
  - DOMAIN-SUFFIX,primevideo.com,🎬 Streaming
  - DOMAIN-SUFFIX,dazn.com,🎬 Streaming
  - DOMAIN-SUFFIX,crunchyroll.com,🎬 Streaming
  - DOMAIN-SUFFIX,tiktok.com,🎬 Streaming

  # ── Direct Services ───────────────────────────────────────────────────────
  - RULE-SET,Apple,DIRECT
  - RULE-SET,GoogleCN,DIRECT

  # ── Telegram → Master Selector ────────────────────────────────────────────
  - RULE-SET,Telegram,🎯 zorVPN

  # ── Social & Dev → Master Selector ────────────────────────────────────────
  - DOMAIN-SUFFIX,twitter.com,🎯 zorVPN
  - DOMAIN-SUFFIX,x.com,🎯 zorVPN
  - DOMAIN-SUFFIX,instagram.com,🎯 zorVPN
  - DOMAIN-SUFFIX,facebook.com,🎯 zorVPN
  - DOMAIN-SUFFIX,whatsapp.com,🎯 zorVPN
  - DOMAIN-SUFFIX,discord.com,🎯 zorVPN
  - DOMAIN-SUFFIX,reddit.com,🎯 zorVPN
  - DOMAIN-SUFFIX,github.com,🎯 zorVPN
  - DOMAIN-SUFFIX,githubusercontent.com,🎯 zorVPN
  - DOMAIN-SUFFIX,stackoverflow.com,🎯 zorVPN
  - DOMAIN-SUFFIX,docker.io,🎯 zorVPN
  - DOMAIN-SUFFIX,npmjs.com,🎯 zorVPN

  # ── Google Global ─────────────────────────────────────────────────────────
  - DOMAIN-SUFFIX,google.com,🎯 zorVPN
  - DOMAIN-SUFFIX,googleapis.com,🎯 zorVPN
  - DOMAIN-SUFFIX,gstatic.com,🎯 zorVPN
  - DOMAIN-SUFFIX,gmail.com,🎯 zorVPN

  # ── General Proxy List ────────────────────────────────────────────────────
  - RULE-SET,ProxyLite,🎯 zorVPN

  # ── Direct Chinese Traffic ────────────────────────────────────────────────
  - RULE-SET,ChinaDomain,DIRECT
  - GEOIP,CN,DIRECT

  # ── Final Fallback ────────────────────────────────────────────────────────
  - MATCH,🎯 zorVPN
"""

    full_output = header + "\n" + yaml_proxies + "\n" + yaml_groups + "\n" + rules_section

    with open(OUTPUT_YAML, 'w', encoding='utf-8') as f:
        f.write(full_output)

    print(f"\n{'═' * 70}")
    print(f"  🎉 SUCCESS! zorVPN configuration written to: {OUTPUT_YAML}")
    print(f"  Total Proxies   : {len(renamed_proxies)}")
    print(f"  Total Groups    : {len(proxy_groups)}")
    print(f"  Countries       : {len(region_pools)}")
    print(f"  File Size       : {os.path.getsize(OUTPUT_YAML):,} bytes")
    print(f"{'═' * 70}\n")
    return True


if __name__ == '__main__':
    success = build_zorvpn()
    if not success:
        sys.exit(1)
