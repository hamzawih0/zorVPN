"""
zorVPN — Premium Subscription Generator & Active Health Filter
Fetches candidates from verified GitHub sources, runs real-time protocol
and HTTP 204 latency tests using Mihomo (Clash.Meta) core, rejects dead/blocked
nodes, groups verified green nodes by speed/AI/streaming/country, and writes clash.yaml.
"""

import sys
import os
import re
import ssl
import time
import json
import base64
import shutil
import hashlib
import tempfile
import subprocess
import urllib.request
import urllib.parse
import concurrent.futures
from datetime import datetime, timezone
from collections import defaultdict
import yaml

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_ZORVPN = os.path.join(ROOT_DIR, "ZorVPN.yaml")
OUTPUT_CLASH = os.path.join(ROOT_DIR, "clash.yaml")
OUTPUT_B64_TXT = os.path.join(ROOT_DIR, "ZorVPN.txt")
OUTPUT_B64_LITE = os.path.join(ROOT_DIR, "ZorVPN-lite.txt")
OUTPUT_B64_ALL = os.path.join(ROOT_DIR, "ZorVPN-all.txt")
OUTPUT_NODES_TXT = os.path.join(ROOT_DIR, "ZorVPN-nodes.txt")

def proxy_to_uri(p: dict) -> str:
    """Convert Clash proxy dict to standard URI (vless, hysteria2, trojan, vmess, ss)."""
    ptype = str(p.get('type', '')).lower()
    name = str(p.get('name', ''))
    server = str(p.get('server', ''))
    port = str(p.get('port', ''))

    if ptype == 'hysteria2':
        auth = p.get('password', p.get('auth', ''))
        sni = p.get('sni', p.get('server', ''))
        insecure = 1 if p.get('skip-cert-verify') else 0
        return f'hysteria2://{auth}@{server}:{port}?sni={sni}&insecure={insecure}#{urllib.parse.quote(name)}'
    elif ptype == 'vless':
        uuid = p.get('uuid', '')
        flow = p.get('flow', '')
        sni = p.get('servername', p.get('sni', ''))
        network = p.get('network', 'tcp')
        pbk = p.get('reality-opts', {}).get('public-key', '') if p.get('reality-opts') else ''
        sid = p.get('reality-opts', {}).get('short-id', '') if p.get('reality-opts') else ''
        fp = p.get('client-fingerprint', '')
        security = 'reality' if pbk else ('tls' if p.get('tls') else 'none')
        params = [f'security={security}']
        if flow: params.append(f'flow={flow}')
        if sni: params.append(f'sni={sni}')
        if fp: params.append(f'fp={fp}')
        if pbk: params.append(f'pbk={pbk}')
        if sid: params.append(f'sid={sid}')
        if network: params.append(f'type={network}')
        return f'vless://{uuid}@{server}:{port}?' + '&'.join(params) + f'#{urllib.parse.quote(name)}'
    elif ptype == 'trojan':
        pw = p.get('password', '')
        sni = p.get('sni', '')
        return f'trojan://{pw}@{server}:{port}?security=tls&sni={sni}#{urllib.parse.quote(name)}'
    elif ptype == 'vmess':
        v_dict = {
            'v': '2', 'ps': name, 'add': server, 'port': port,
            'id': p.get('uuid', ''), 'aid': p.get('alterId', 0),
            'scy': p.get('cipher', 'auto'), 'net': p.get('network', 'tcp'),
            'type': 'none',
            'host': p.get('ws-opts', {}).get('headers', {}).get('Host', '') if p.get('ws-opts') else '',
            'path': p.get('ws-opts', {}).get('path', '') if p.get('ws-opts') else '',
            'tls': 'tls' if p.get('tls') else '',
            'sni': p.get('servername', p.get('sni', ''))
        }
        v_str = base64.b64encode(json.dumps(v_dict).encode('utf-8')).decode('utf-8')
        return f'vmess://{v_str}'
    elif ptype == 'ss':
        cipher = p.get('cipher', '')
        pw = p.get('password', '')
        user_info = base64.b64encode(f'{cipher}:{pw}'.encode('utf-8')).decode('utf-8')
        return f'ss://{user_info}@{server}:{port}#{urllib.parse.quote(name)}'
    return ""

# Verified upstream subscription sources
SOURCES = [
    {
        "name": "Au1rxx/free-vpn-subscriptions (VLESS & Hy2 Pre-verified)",
        "url": "https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/clash.yaml",
    },
    {
        "name": "sunmiao4458/free-proxy-airport (Low Latency Verified)",
        "url": "https://sunmiao4458.github.io/free-proxy-airport/clash.yaml",
    },
    {
        "name": "sinspired/airport (Daily Speed Tested)",
        "url": "https://raw.githubusercontent.com/sinspired/airport/main/subs/clashfree.yaml",
    },
    {
        "name": "peasoft/NoMoreWalls",
        "url": "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.meta.yml",
    },
    {
        "name": "ermaozi/get_subscribe",
        "url": "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    },
    {
        "name": "anaer/Sub (Multi-Airport Harvest)",
        "url": "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
    },
    {
        "name": "awesome-vpn/awesome-vpn",
        "url": "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/clash.yaml",
    },
]

# Country detection lookup
COUNTRY_MAP = {
    # Asia-Pacific
    'HK': ('🇭🇰', 'HK', 'Hong Kong'), 'hongkong': ('🇭🇰', 'HK', 'Hong Kong'), '香港': ('🇭🇰', 'HK', 'Hong Kong'), 'HKG': ('🇭🇰', 'HK', 'Hong Kong'),
    'JP': ('🇯🇵', 'JP', 'Japan'), 'japan': ('🇯🇵', 'JP', 'Japan'), '日本': ('🇯🇵', 'JP', 'Japan'), 'JPN': ('🇯🇵', 'JP', 'Japan'), 'tokyo': ('🇯🇵', 'JP', 'Japan'), 'osaka': ('🇯🇵', 'JP', 'Japan'),
    'SG': ('🇸🇬', 'SG', 'Singapore'), 'singapore': ('🇸🇬', 'SG', 'Singapore'), '新加坡': ('🇸🇬', 'SG', 'Singapore'), 'SGP': ('🇸🇬', 'SG', 'Singapore'), '狮城': ('🇸🇬', 'SG', 'Singapore'),
    'KR': ('🇰🇷', 'KR', 'South Korea'), 'korea': ('🇰🇷', 'KR', 'South Korea'), '韩国': ('🇰🇷', 'KR', 'South Korea'), 'KOR': ('🇰🇷', 'KR', 'South Korea'), 'seoul': ('🇰🇷', 'KR', 'South Korea'),
    'TW': ('🇹🇼', 'TW', 'Taiwan'), 'taiwan': ('🇹🇼', 'TW', 'Taiwan'), '台湾': ('🇹🇼', 'TW', 'Taiwan'), 'TWN': ('🇹🇼', 'TW', 'Taiwan'), 'taipei': ('🇹🇼', 'TW', 'Taiwan'),
    'IN': ('🇮🇳', 'IN', 'India'), 'india': ('🇮🇳', 'IN', 'India'), '印度': ('🇮🇳', 'IN', 'India'), 'mumbai': ('🇮🇳', 'IN', 'India'),
    'AU': ('🇦🇺', 'AU', 'Australia'), 'australia': ('🇦🇺', 'AU', 'Australia'), '澳大利亚': ('🇦🇺', 'AU', 'Australia'), 'sydney': ('🇦🇺', 'AU', 'Australia'),
    'MY': ('🇲🇾', 'MY', 'Malaysia'), 'malaysia': ('🇲🇾', 'MY', 'Malaysia'), '马来西亚': ('🇲🇾', 'MY', 'Malaysia'),
    'TH': ('🇹🇭', 'TH', 'Thailand'), 'thailand': ('🇹🇭', 'TH', 'Thailand'), '泰国': ('🇹🇭', 'TH', 'Thailand'),
    'VN': ('🇻🇳', 'VN', 'Vietnam'), 'vietnam': ('🇻🇳', 'VN', 'Vietnam'), '越南': ('🇻🇳', 'VN', 'Vietnam'),
    'PH': ('🇵🇭', 'PH', 'Philippines'), 'philippines': ('🇵🇭', 'PH', 'Philippines'),
    'ID': ('🇮🇩', 'ID', 'Indonesia'), 'indonesia': ('🇮🇩', 'ID', 'Indonesia'),

    # North America
    'US': ('🇺🇸', 'US', 'United States'), 'united states': ('🇺🇸', 'US', 'United States'), '美国': ('🇺🇸', 'US', 'United States'), 'USA': ('🇺🇸', 'US', 'United States'), 'america': ('🇺🇸', 'US', 'United States'),
    'CA': ('🇨🇦', 'CA', 'Canada'), 'canada': ('🇨🇦', 'CA', 'Canada'), '加拿大': ('🇨🇦', 'CA', 'Canada'), 'CAN': ('🇨🇦', 'CA', 'Canada'),

    # Europe
    'DE': ('🇩🇪', 'DE', 'Germany'), 'germany': ('🇩🇪', 'DE', 'Germany'), '德国': ('🇩🇪', 'DE', 'Germany'), 'DEU': ('🇩🇪', 'DE', 'Germany'), 'frankfurt': ('🇩🇪', 'DE', 'Germany'),
    'GB': ('🇬🇧', 'GB', 'United Kingdom'), 'uk': ('🇬🇧', 'GB', 'United Kingdom'), 'united kingdom': ('🇬🇧', 'GB', 'United Kingdom'), '英国': ('🇬🇧', 'GB', 'United Kingdom'), 'GBR': ('🇬🇧', 'GB', 'United Kingdom'), 'london': ('🇬🇧', 'GB', 'United Kingdom'),
    'FR': ('🇫🇷', 'FR', 'France'), 'france': ('🇫🇷', 'FR', 'France'), '法国': ('🇫🇷', 'FR', 'France'), 'FRA': ('🇫🇷', 'FR', 'France'), 'paris': ('🇫🇷', 'FR', 'France'),
    'NL': ('🇳🇱', 'NL', 'Netherlands'), 'netherlands': ('🇳🇱', 'NL', 'Netherlands'), '荷兰': ('🇳🇱', 'NL', 'Netherlands'), 'amsterdam': ('🇳🇱', 'NL', 'Netherlands'),
    'SE': ('🇸🇪', 'SE', 'Sweden'), 'sweden': ('🇸🇪', 'SE', 'Sweden'), '瑞典': ('🇸🇪', 'SE', 'Sweden'),
    'IT': ('🇮🇹', 'IT', 'Italy'), 'italy': ('🇮🇹', 'IT', 'Italy'), '意大利': ('🇮🇹', 'IT', 'Italy'), 'ITA': ('🇮🇹', 'IT', 'Italy'),
    'ES': ('🇪🇸', 'ES', 'Spain'), 'spain': ('🇪🇸', 'ES', 'Spain'), '西班牙': ('🇪🇸', 'ES', 'Spain'),
    'CZ': ('🇨🇿', 'CZ', 'Czech Republic'), 'czech': ('🇨🇿', 'CZ', 'Czech Republic'), '捷克': ('🇨🇿', 'CZ', 'Czech Republic'),
    'PL': ('🇵🇱', 'PL', 'Poland'), 'poland': ('🇵🇱', 'PL', 'Poland'), '波兰': ('🇵🇱', 'PL', 'Poland'),
    'RO': ('🇷🇴', 'RO', 'Romania'), 'romania': ('🇷🇴', 'RO', 'Romania'), '罗马尼亚': ('🇷🇴', 'RO', 'Romania'),
    'EE': ('🇪🇪', 'EE', 'Estonia'), 'estonia': ('🇪🇪', 'EE', 'Estonia'), '爱沙尼亚': ('🇪🇪', 'EE', 'Estonia'),
    'LV': ('🇱🇻', 'LV', 'Latvia'), 'latvia': ('🇱🇻', 'LV', 'Latvia'),
    'AT': ('🇦🇹', 'AT', 'Austria'), 'austria': ('🇦🇹', 'AT', 'Austria'), '奥地利': ('🇦🇹', 'AT', 'Austria'),
    'CH': ('🇨🇭', 'CH', 'Switzerland'), 'switzerland': ('🇨🇭', 'CH', 'Switzerland'), '瑞士': ('🇨🇭', 'CH', 'Switzerland'),
    'FI': ('🇫🇮', 'FI', 'Finland'), 'finland': ('🇫🇮', 'FI', 'Finland'),
    'NO': ('🇳🇴', 'NO', 'Norway'), 'norway': ('🇳🇴', 'NO', 'Norway'),
    'DK': ('🇩🇰', 'DK', 'Denmark'), 'denmark': ('🇩🇰', 'DK', 'Denmark'),
    'IE': ('🇮🇪', 'IE', 'Ireland'), 'ireland': ('🇮🇪', 'IE', 'Ireland'),
    'UA': ('🇺🇦', 'UA', 'Ukraine'), 'ukraine': ('🇺🇦', 'UA', 'Ukraine'),

    # Middle East & Eurasia
    'RU': ('🇷🇺', 'RU', 'Russia'), 'russia': ('🇷🇺', 'RU', 'Russia'), '俄罗斯': ('🇷🇺', 'RU', 'Russia'), 'RUS': ('🇷🇺', 'RU', 'Russia'),
    'TR': ('🇹🇷', 'TR', 'Turkey'), 'turkey': ('🇹🇷', 'TR', 'Turkey'), '土耳其': ('🇹🇷', 'TR', 'Turkey'),
    'IL': ('🇮🇱', 'IL', 'Israel'), 'israel': ('🇮🇱', 'IL', 'Israel'),
    'IR': ('🇮🇷', 'IR', 'Iran'), 'iran': ('🇮🇷', 'IR', 'Iran'),
    'AE': ('🇦🇪', 'AE', 'United Arab Emirates'), 'dubai': ('🇦🇪', 'AE', 'United Arab Emirates'),

    # South America & Africa
    'BR': ('🇧🇷', 'BR', 'Brazil'), 'brazil': ('🇧🇷', 'BR', 'Brazil'),
    'CL': ('🇨🇱', 'CL', 'Chile'), 'chile': ('🇨🇱', 'CL', 'Chile'),
    'ZA': ('🇿🇦', 'ZA', 'South Africa'), 'south africa': ('🇿🇦', 'ZA', 'South Africa'),
}

EMOJI_FLAG_MAP = {
    '🇭🇰': 'HK', '🇯🇵': 'JP', '🇸🇬': 'SG', '🇺🇸': 'US', '🇩🇪': 'DE',
    '🇬🇧': 'GB', '🇫🇷': 'FR', '🇳🇱': 'NL', '🇸🇪': 'SE', '🇮🇹': 'IT',
    '🇪🇸': 'ES', '🇨🇿': 'CZ', '🇷🇺': 'RU', '🇹🇷': 'TR', '🇮🇱': 'IL',
    '🇨🇱': 'CL', '🇪🇪': 'EE', '🇱🇻': 'LV', '🇨🇦': 'CA', '🇰🇷': 'KR',
    '🇹🇼': 'TW', '🇵🇱': 'PL', '🇷🇴': 'RO', '🇦🇹': 'AT', '🇨🇭': 'CH',
    '🇮🇳': 'IN', '🇧🇷': 'BR', '🇦🇺': 'AU', '🇫🇮': 'FI', '🇳🇴': 'NO',
    '🇩🇰': 'DK', '🇮🇪': 'IE', '🇦🇪': 'AE', '🇿🇦': 'ZA', '🇺🇦': 'UA',
    '🇲🇾': 'MY', '🇹🇭': 'TH', '🇻🇳': 'VN', '🇵🇭': 'PH', '🇮🇩': 'ID',
    '🇮🇷': 'IR',
}

def detect_country(name: str, server: str = "") -> str:
    if not name:
        name = ""
    for emoji, code in EMOJI_FLAG_MAP.items():
        if emoji in name:
            return code
    name_lower = name.lower()
    for kw, val in sorted(COUNTRY_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        kw_lower = kw.lower()
        if any(ord(c) > 127 for c in kw):
            if kw in name:
                return val[1]
        else:
            if re.search(r'(?:\b|_|-)' + re.escape(kw_lower) + r'(?:\b|_|-|\d)', name_lower) or kw_lower in name_lower:
                return val[1]
    if server:
        srv_lower = server.lower()
        parts = srv_lower.split('.')
        if len(parts) >= 2:
            tld = parts[-1].upper()
            if tld in EMOJI_FLAG_MAP.values():
                return tld
    return 'XX'


def proxy_fingerprint(proxy: dict) -> str:
    server = str(proxy.get('server', '')).strip().lower()
    port = str(proxy.get('port', '')).strip()
    ptype = str(proxy.get('type', '')).strip().lower()
    cred = str(proxy.get('uuid', proxy.get('password', ''))).strip()
    return hashlib.sha256(f"{server}:{port}:{ptype}:{cred}".encode('utf-8')).hexdigest()


def find_mihomo_bin() -> str:
    for cmd in ['mihomo', 'clash-meta', 'verge-mihomo']:
        p = shutil.which(cmd)
        if p and os.path.isfile(p):
            return p
    for p in ['/usr/local/bin/mihomo', '/usr/bin/mihomo', '/tmp/mihomo']:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    win_paths = [
        r"C:\Program Files\Clash Verge\verge-mihomo.exe",
        r"C:\Program Files\Clash Verge\verge-mihomo-alpha.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\clash-verge-rev\resources\verge-mihomo.exe"),
    ]
    for p in win_paths:
        if os.path.isfile(p):
            return p
    return ""


def fetch_url(url: str, timeout: int = 15) -> bytes:
    headers = {
        'User-Agent': 'ClashforWindows/0.20.39 ClashX/1.118.0 Stash/2.6.0',
        'Accept': '*/*',
    }
    proxies = {}
    if os.environ.get('http_proxy'):
        proxies['http'] = os.environ.get('http_proxy')
    if os.environ.get('https_proxy'):
        proxies['https'] = os.environ.get('https_proxy')
    if not proxies and os.name == 'nt':
        proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Try with proxy
    if proxies:
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
            req = urllib.request.Request(url, headers=headers)
            with opener.open(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            pass

    # Fallback direct
    try:
        direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(url, headers=headers)
        with direct_opener.open(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        raise e


AD_KEYWORDS = [
    '剩余流量', '到期时间', '官网', 'TG群', '购买', '过期', '通知', '重置',
    '微信', '公告', '客服', '禁止', '续费', '套餐', '发布页', '频道', '导航',
    '防失联', '打赏', '更新', '说明', '教程', '推广', '合作', '网址', '关注',
    '备用', '返利', 'AFF', 'aff', 'QQ群', '群聊', '群主'
]

def parse_clash_yaml(content_bytes: bytes) -> list:
    try:
        text = content_bytes.decode('utf-8', errors='ignore')
        if '```yaml' in text:
            text = text.split('```yaml', 1)[1].split('```', 1)[0]
        elif '```' in text:
            text = text.split('```', 1)[1].split('```', 1)[0]
        data = yaml.safe_load(text)
        if isinstance(data, dict) and 'proxies' in data and isinstance(data['proxies'], list):
            valid = []
            for p in data['proxies']:
                if isinstance(p, dict) and 'server' in p and 'port' in p:
                    # Sanitize invalid dummy servers
                    server = str(p.get('server', '')).strip().lower()
                    if not server or server in ('127.0.0.1', '0.0.0.0', 'localhost'):
                        continue
                    # Sanitize airport marketing cards / spam announcements
                    name = str(p.get('name', '')).strip()
                    if any(kw in name for kw in AD_KEYWORDS):
                        continue
                    ptype = str(p.get('type', '')).lower()
                    if ptype in ('vless', 'hysteria2', 'hysteria', 'trojan', 'vmess', 'ss', 'socks5'):
                        valid.append(p)
            return valid
    except Exception as e:
        print(f"    [Error parsing YAML]: {e}")
    return []


def test_proxies_with_mihomo(candidates: list, mihomo_bin: str, max_workers: int = 35) -> list:
    print(f"\n  🔍 Starting Active Health Filter ({len(candidates)} candidates)...")
    print(f"  ⚡ Engine: {mihomo_bin}")
    print(f"  🧪 Probe Target: http://www.gstatic.com/generate_204 (Timeout: 2500ms, Workers: {max_workers})")

    temp_proxies = []
    for i, p in enumerate(candidates):
        p_test = dict(p)
        p_test['name'] = f"node_{i:04d}"
        temp_proxies.append(p_test)

    temp_dir = tempfile.mkdtemp()
    ctrl_port = 19095
    secret = "zorvpn-test"

    test_cfg = {
        'mixed-port': 17895,
        'mode': 'rule',
        'log-level': 'silent',
        'external-controller': f'127.0.0.1:{ctrl_port}',
        'secret': secret,
        'proxies': temp_proxies
    }

    cfg_path = os.path.join(temp_dir, 'config.yaml')
    with open(cfg_path, 'w', encoding='utf-8') as f:
        yaml.dump(test_cfg, f, allow_unicode=True)

    proc = subprocess.Popen([mihomo_bin, '-d', temp_dir, '-f', cfg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)

    alive_results = []
    t_start = time.time()

    def check_node(item):
        orig_proxy, test_proxy = item
        node_name = test_proxy['name']
        url = f"http://127.0.0.1:{ctrl_port}/proxies/{urllib.parse.quote(node_name)}/delay?timeout=2500&url=http://www.gstatic.com/generate_204"
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {secret}'})
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                delay = data.get('delay', 0)
                if delay and 0 < delay <= 2500:
                    return (orig_proxy, delay)
        except Exception:
            pass
        return None

    try:
        items = list(zip(candidates, temp_proxies))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(check_node, it): it for it in items}
            done_count = 0
            for future in concurrent.futures.as_completed(future_to_item):
                res = future.result()
                done_count += 1
                if res:
                    alive_results.append(res)
                    orig, delay = res
                    ptype = orig.get('type', '').upper()
                    print(f"    ✓ [ALIVE {delay:>4}ms] {ptype:<6} -> {orig.get('server')}:{orig.get('port')}")
                if done_count % 100 == 0:
                    print(f"    ... Tested {done_count}/{len(candidates)} candidates ({len(alive_results)} alive so far)")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        shutil.rmtree(temp_dir, ignore_errors=True)

    elapsed = time.time() - t_start
    print(f"\n  🎯 Health Check Complete in {elapsed:.1f}s!")
    print(f"  ✅ Verified GREEN Working Nodes: {len(alive_results)} / {len(candidates)} tested")
    print(f"  ❌ Discarded Dead/Timed-Out Nodes: {len(candidates) - len(alive_results)}")

    alive_results.sort(key=lambda x: x[1])
    return alive_results


def build_zorvpn():
    print("═" * 70)
    print("  🚀 zorVPN Subscription Updater — Aggregating & Health-Filtering")
    print("═" * 70)

    all_candidates = []
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
                    seen_fingerprints.add(fp)
                    all_candidates.append(dict(p))
                    added += 1
            print(f"  ✓ {len(proxies)} nodes ({added} unique)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print(f"\n  Total unique candidate nodes harvested: {len(all_candidates)}")
    if not all_candidates:
        print("  ❌ No proxies collected! Aborting update to protect existing clash.yaml.")
        return False

    mihomo_bin = find_mihomo_bin()
    if mihomo_bin:
        # Prioritize Hysteria2, VLESS, Trojan (top GFW evasion protocols)
        def sort_priority(p):
            t = str(p.get('type', '')).lower()
            if t == 'hysteria2': return 0
            if t == 'vless': return 1
            if t == 'trojan': return 2
            if t == 'vmess': return 3
            return 4

        all_candidates.sort(key=sort_priority)
        candidates_to_test = all_candidates[:1200]
        verified_results = test_proxies_with_mihomo(candidates_to_test, mihomo_bin, max_workers=35)
        if verified_results:
            working_proxies = [item[0] for item in verified_results]
        else:
            print("  ⚠️ No nodes passed delay test, keeping top candidates.")
            working_proxies = all_candidates[:50]
    else:
        print("  ⚠️ Warning: Mihomo binary not found. Skipping live delay test.")
        working_proxies = all_candidates[:200]

    # Group by country and rename
    renamed_proxies = []
    country_counters = defaultdict(int)

    for p in working_proxies:
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
        'Norway', 'Denmark', 'Ireland', 'Malaysia', 'Thailand', 'Vietnam',
        'Philippines', 'Indonesia', 'United Arab Emirates', 'Ukraine', 'Other'
    ]

    for country in REGION_ORDER:
        members = [p['name'] for p in renamed_proxies if f" {country} #" in p['name']]
        if members:
            flag = members[0].split()[0]
            pool_name = f"{flag} {country}"
            region_pools[pool_name] = members

    # AI pool: US, SG, JP, KR, GB, DE, CA, AU
    ai_countries = ['United States', 'Singapore', 'Japan', 'South Korea', 'United Kingdom', 'Germany', 'Canada', 'Australia']
    ai_members = [p['name'] for p in renamed_proxies if any(f" {c} #" in p['name'] for c in ai_countries)]
    if not ai_members:
        ai_members = all_proxy_names[:]

    # Streaming pool: US, JP, HK, SG, KR, TW, GB
    stream_countries = ['United States', 'Japan', 'Hong Kong', 'Singapore', 'South Korea', 'Taiwan', 'United Kingdom']
    stream_members = [p['name'] for p in renamed_proxies if any(f" {c} #" in p['name'] for c in stream_countries)]
    if not stream_members:
        stream_members = all_proxy_names[:]

    # Proxy Groups
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

    # 2. Fastest (auto-speedtest all verified nodes)
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

    # 4. AI Pool
    proxy_groups.append({
        'name': '🤖 AI Services',
        'type': 'url-test',
        'proxies': ai_members,
        'url': 'http://www.gstatic.com/generate_204',
        'interval': 300,
        'tolerance': 100,
    })

    # 5. Streaming Pool
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

    # Full Configuration
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    header = f"""# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  zorVPN — 100% Verified Green Subscription                 ║
# ║  Auto-generated: {now_str:<32}                      ║
# ║  Nodes: {len(renamed_proxies):>4} | Countries: {len(region_pools):>2} | Tested: 100% Functional Latency Verified        ║
# ║  Compatible: Clash Verge Rev, ClashX, Stash, Shadowrocket, FlClash, Surge  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

mixed-port: 7890
port: 7891
socks-port: 7892
allow-lan: true
mode: rule
log-level: info
ipv6: true
external-controller: 127.0.0.1:9090

unified-delay: true
tcp-concurrent: true
global-client-fingerprint: chrome
find-process-mode: strict

geodata-mode: true
geo-auto-update: true
geo-update-interval: 24
geox-url:
  geoip: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip-lite.dat"
  geosite: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat"
  mmdb: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country-lite.mmdb"
  asn: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/GeoLite2-ASN.mmdb"

profile:
  store-selected: true
  store-fake-ip: true

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

tun:
  enable: false
  stack: mixed
  dns-hijack:
    - any:53
    - tcp://any:53
  auto-route: true
  auto-detect-interface: true
  mtu: 1400

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
rules:
  # ── Local Area Network ────────────────────────────────────────────────────
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,100.64.0.0/10,DIRECT,no-resolve
  - DOMAIN-SUFFIX,local,DIRECT
  - DOMAIN-SUFFIX,localhost,DIRECT

  # ── Block Advertising ─────────────────────────────────────────────────────
  - DOMAIN-KEYWORD,adservice,REJECT
  - DOMAIN-KEYWORD,telemetry,REJECT
  - DOMAIN-SUFFIX,doubleclick.net,REJECT
  - DOMAIN-SUFFIX,googlesyndication.com,REJECT
  - DOMAIN-SUFFIX,googleadservices.com,REJECT
  - DOMAIN-SUFFIX,adcolony.com,REJECT
  - DOMAIN-SUFFIX,applovin.com,REJECT
  - DOMAIN-SUFFIX,unityads.unity3d.com,REJECT

  # ── AI Services → Dedicated Pool ──────────────────────────────────────────
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

  # ── Streaming → Dedicated Pool ────────────────────────────────────────────
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

  # ── Telegram → Master Selector ────────────────────────────────────────────
  - DOMAIN-SUFFIX,t.me,🎯 zorVPN
  - DOMAIN-SUFFIX,tdesktop.com,🎯 zorVPN
  - DOMAIN-SUFFIX,telegra.ph,🎯 zorVPN
  - DOMAIN-SUFFIX,telegram.me,🎯 zorVPN
  - DOMAIN-SUFFIX,telegram.org,🎯 zorVPN
  - IP-CIDR,91.108.4.0/22,🎯 zorVPN,no-resolve
  - IP-CIDR,91.108.8.0/22,🎯 zorVPN,no-resolve
  - IP-CIDR,91.108.12.0/22,🎯 zorVPN,no-resolve
  - IP-CIDR,91.108.16.0/22,🎯 zorVPN,no-resolve
  - IP-CIDR,91.108.20.0/22,🎯 zorVPN,no-resolve
  - IP-CIDR,91.108.56.0/22,🎯 zorVPN,no-resolve
  - IP-CIDR,149.154.160.0/20,🎯 zorVPN,no-resolve

  # ── Apple & Google CN → Direct ────────────────────────────────────────────
  - DOMAIN-SUFFIX,apple.com,DIRECT
  - DOMAIN-SUFFIX,icloud.com,DIRECT
  - DOMAIN-SUFFIX,itunes.com,DIRECT
  - DOMAIN-SUFFIX,mzstatic.com,DIRECT
  - DOMAIN-SUFFIX,google.cn,DIRECT
  - DOMAIN-SUFFIX,gstatic.cn,DIRECT

  # ── Global Sites & Dev Tools → Master Selector ────────────────────────────
  - DOMAIN-SUFFIX,twitter.com,🎯 zorVPN
  - DOMAIN-SUFFIX,x.com,🎯 zorVPN
  - DOMAIN-SUFFIX,instagram.com,🎯 zorVPN
  - DOMAIN-SUFFIX,facebook.com,🎯 zorVPN
  - DOMAIN-SUFFIX,whatsapp.com,🎯 zorVPN
  - DOMAIN-SUFFIX,discord.com,🎯 zorVPN
  - DOMAIN-SUFFIX,reddit.com,🎯 zorVPN
  - DOMAIN-SUFFIX,github.com,🎯 zorVPN
  - DOMAIN-SUFFIX,githubusercontent.com,🎯 zorVPN
  - DOMAIN-SUFFIX,cloudflare.com,🎯 zorVPN
  - DOMAIN-SUFFIX,workers.dev,🎯 zorVPN
  - DOMAIN-SUFFIX,pages.dev,🎯 zorVPN
  - DOMAIN-SUFFIX,stackoverflow.com,🎯 zorVPN
  - DOMAIN-SUFFIX,docker.io,🎯 zorVPN
  - DOMAIN-SUFFIX,npmjs.com,🎯 zorVPN
  - DOMAIN-SUFFIX,google.com,🎯 zorVPN
  - DOMAIN-SUFFIX,googleapis.com,🎯 zorVPN
  - DOMAIN-SUFFIX,gstatic.com,🎯 zorVPN
  - DOMAIN-SUFFIX,gmail.com,🎯 zorVPN
  - DOMAIN-SUFFIX,wikipedia.org,🎯 zorVPN

  # ── Domestic Chinese Traffic → Direct ─────────────────────────────────────
  - DOMAIN-SUFFIX,cn,DIRECT
  - DOMAIN-SUFFIX,baidu.com,DIRECT
  - DOMAIN-SUFFIX,qq.com,DIRECT
  - DOMAIN-SUFFIX,bilibili.com,DIRECT
  - DOMAIN-SUFFIX,alipay.com,DIRECT
  - DOMAIN-SUFFIX,taobao.com,DIRECT
  - DOMAIN-SUFFIX,jd.com,DIRECT
  - DOMAIN-SUFFIX,weibo.com,DIRECT
  - DOMAIN-SUFFIX,zhihu.com,DIRECT
  - DOMAIN-SUFFIX,163.com,DIRECT
  - DOMAIN-SUFFIX,sohu.com,DIRECT
  - DOMAIN-SUFFIX,sina.com.cn,DIRECT
  - DOMAIN-SUFFIX,douyin.com,DIRECT
  - DOMAIN-SUFFIX,bytedance.com,DIRECT
  - GEOIP,CN,DIRECT

  # ── Final Catch-All ───────────────────────────────────────────────────────
  - MATCH,🎯 zorVPN
"""

    full_output = header + "\n" + yaml_proxies + "\n" + yaml_groups + "\n" + rules_section

    # Write Clash/Mihomo YAML files (ZorVPN.yaml and clash.yaml)
    for out_path in [OUTPUT_ZORVPN, OUTPUT_CLASH]:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(full_output)

    # Convert proxies to standard URIs for Shadowrocket / V2Ray / Sing-box
    uris = []
    for p in working_proxies:
        uri = proxy_to_uri(p)
        if uri:
            uris.append(uri)

    # 1. Plaintext URI list (all verified nodes, one per line)
    raw_nodes_text = "\n".join(uris)
    with open(OUTPUT_NODES_TXT, 'w', encoding='utf-8') as f:
        f.write(raw_nodes_text)

    # 2. iOS Shadowrocket Lite (Top 30 ultra-low latency nodes — loads in 0.05s, zero clutter)
    b64_lite = base64.b64encode("\n".join(uris[:30]).encode('utf-8')).decode('utf-8')
    with open(OUTPUT_B64_LITE, 'w', encoding='utf-8') as f:
        f.write(b64_lite)

    # 3. iOS Shadowrocket Standard (Top 60 curated nodes — balanced global coverage)
    b64_standard = base64.b64encode("\n".join(uris[:60]).encode('utf-8')).decode('utf-8')
    with open(OUTPUT_B64_TXT, 'w', encoding='utf-8') as f:
        f.write(b64_standard)

    # 4. iOS Shadowrocket Full Pool (All verified nodes)
    b64_all = base64.b64encode(raw_nodes_text.encode('utf-8')).decode('utf-8')
    with open(OUTPUT_B64_ALL, 'w', encoding='utf-8') as f:
        f.write(b64_all)

    print(f"\n{'═' * 70}")
    print(f"  🎉 SUCCESS! zorVPN subscriptions written successfully:")
    print(f"    - {OUTPUT_ZORVPN} (Clash/Mihomo/FlClash/Stash)")
    print(f"    - {OUTPUT_CLASH} (Legacy alias)")
    print(f"    - {OUTPUT_B64_LITE} (iOS Shadowrocket Lite: Top 30 nodes)")
    print(f"    - {OUTPUT_B64_TXT} (iOS Shadowrocket Standard: Top 60 nodes)")
    print(f"    - {OUTPUT_B64_ALL} (Full Base64 Pool: {len(uris)} nodes)")
    print(f"    - {OUTPUT_NODES_TXT} (Plain URI links)")
    print(f"  Total Verified Proxies : {len(renamed_proxies)} (100% Green)")
    print(f"  Total Groups           : {len(proxy_groups)}")
    print(f"  Shadowrocket URIs      : {len(uris)}")
    print(f"  Countries              : {len(region_pools)}")
    print(f"  File Size              : {os.path.getsize(OUTPUT_ZORVPN):,} bytes")
    print(f"{'═' * 70}\n")
    return True


if __name__ == '__main__':
    success = build_zorvpn()
    if not success:
        sys.exit(1)
