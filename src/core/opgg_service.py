"""op.gg rank fetching service"""
import json
import re
from urllib.parse import quote

import requests

# Map internal region codes to op.gg URL slugs
OPGG_REGION_MAP = {
    "NA": "na",
    "EUW": "euw",
    "EUNE": "eune",
    "KR": "kr",
    "JP": "jp",
    "OCE": "oce",
    "BR": "br",
    "LAN": "lan",
    "LAS": "las",
    "RU": "ru",
    "TR": "tr",
    "ME": "me",
    "PH": "ph",
    "SG": "sg",
    "TH": "th",
    "TW": "tw",
    "VN": "vn",
    "CN": "cn",
    "PBE": "pbe",
}

TIER_DISPLAY = {
    "IRON": "Iron",
    "BRONZE": "Bronze",
    "SILVER": "Silver",
    "GOLD": "Gold",
    "PLATINUM": "Platinum",
    "EMERALD": "Emerald",
    "DIAMOND": "Diamond",
    "MASTER": "Master",
    "GRANDMASTER": "Grandmaster",
    "CHALLENGER": "Challenger",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
}


def _extract_next_data(html: str) -> dict:
    """Extract the __NEXT_DATA__ JSON blob from a Next.js page."""
    match = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return {}


def _parse_league_stats(next_data: dict) -> dict | None:
    """
    Walk the __NEXT_DATA__ tree to find solo-queue league stats.
    Returns a dict with keys: tier, division, lp, wins, losses
    or None if not found / unranked.
    """
    try:
        page_props = next_data.get("props", {}).get("pageProps", {})
        data = page_props.get("data", {})

        # op.gg sometimes wraps data under "summoner", sometimes directly
        summoner = data.get("summoner", data)

        league_stats = summoner.get("league_stats") or summoner.get("leagueStats") or []

        for stat in league_stats:
            queue = stat.get("queue_info") or stat.get("queueInfo") or {}
            game_type = queue.get("game_type") or queue.get("gameType") or ""
            if "SOLO" not in game_type.upper():
                continue

            tier_info = stat.get("tier_info") or stat.get("tierInfo") or {}
            tier = (tier_info.get("tier") or "").upper()
            division = tier_info.get("division") or tier_info.get("rank") or ""
            lp = tier_info.get("lp") or tier_info.get("leaguePoints") or 0
            wins = stat.get("win") or stat.get("wins") or 0
            losses = stat.get("lose") or stat.get("losses") or 0

            if tier:
                return {
                    "tier": tier,
                    "division": division,
                    "lp": lp,
                    "wins": wins,
                    "losses": losses,
                }
    except Exception:
        pass
    return None


def fetch_rank(display_name: str, tag_line: str, region: str, timeout: int = 10) -> dict:
    """
    Fetch solo-queue rank data for an account from op.gg.

    Returns a dict with:
        - ``status``: "ok", "unranked", or "error"
        - ``text``:   short display string, e.g. "Gold II  45 LP  80W / 70L"
        - ``tier``, ``division``, ``lp``, ``wins``, ``losses``  (when status=="ok")
        - ``message``:  error description (when status=="error")
    """
    region_slug = OPGG_REGION_MAP.get(region.upper(), region.lower())
    encoded_name = quote(display_name, safe="")
    url = f"https://op.gg/lol/summoners/{region_slug}/{encoded_name}-{tag_line}"

    try:
        response = requests.get(url, headers=_HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Timeout"}
    except requests.exceptions.HTTPError as exc:
        return {"status": "error", "message": f"HTTP {exc.response.status_code}"}
    except requests.exceptions.RequestException as exc:
        return {"status": "error", "message": str(exc)}

    next_data = _extract_next_data(response.text)
    stats = _parse_league_stats(next_data)

    if stats is None:
        return {"status": "unranked", "text": "Unranked"}

    tier_label = TIER_DISPLAY.get(stats["tier"], stats["tier"].capitalize())
    division = stats["division"]
    # Master+ tiers have no division
    div_str = f" {division}" if division and stats["tier"] not in ("MASTER", "GRANDMASTER", "CHALLENGER") else ""

    text = f"{tier_label}{div_str}  {stats['lp']} LP  {stats['wins']}W / {stats['losses']}L"
    return {
        "status": "ok",
        "text": text,
        **stats,
    }
