"""op.gg rank fetching service"""
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

TIER_COLORS = {
    "Iron":        "#7c7c7c",
    "Bronze":      "#cd7f32",
    "Silver":      "#a8a8a8",
    "Gold":        "#f4c430",
    "Platinum":    "#4ead8e",
    "Emerald":     "#50c878",
    "Diamond":     "#5f9ea0",
    "Master":      "#9b59b6",
    "Grandmaster": "#e74c3c",
    "Challenger":  "#f1c40f",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

# op.gg meta description format:
# "Name#Tag / Silver 2 48LP / 13Win 14Lose Win rate 48% / ..."
# (sometimes an extra number appears after division: "Silver 2 2 48LP")
_TIERS = (
    "Challenger", "Grandmaster", "Master",
    "Diamond", "Emerald", "Platinum", "Gold", "Silver", "Bronze", "Iron"
)
_TIER_PAT = "|".join(_TIERS)
_DESC_RE = re.compile(
    rf'({_TIER_PAT})'
    r'(?:\s+(\d+))?'          # optional division numeral (1-4)
    r'(?:\s+\d+)?'            # optional extra number op.gg sometimes inserts
    r'\s+(\d+)LP'
    r'\s*/\s*(\d+)Win\s+(\d+)Lose'
    r'\s+Win rate\s+(\d+)%',
    re.IGNORECASE,
)


def _parse_meta_description(html: str):
    """
    Extract rank info from the og:description / meta description tag.
    Returns a dict or None.
    """
    # Try <meta name="description" content="...">
    meta_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=(["\'])(.*?)\1',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if not meta_match:
        # Also try content-first attribute ordering
        meta_match = re.search(
            r'<meta[^>]+content=(["\'])(.*?)\1[^>]+name=["\']description["\']',
            html,
            re.DOTALL | re.IGNORECASE,
        )
    description = meta_match.group(2) if meta_match else ""

    m = _DESC_RE.search(description)
    if not m:
        return None

    tier = m.group(1).capitalize()
    # Normalise multi-word tiers
    tier = {"Grandmaster": "Grandmaster", "Challenger": "Challenger"}.get(tier, tier)
    division = m.group(2) or ""   # empty for Master+
    lp = int(m.group(3))
    wins = int(m.group(4))
    losses = int(m.group(5))
    win_rate = int(m.group(6))

    div_str = f" {division}" if division else ""
    text = f"{tier}{div_str}  {lp} LP  {wins}W / {losses}L  {win_rate}% WR"
    return {
        "status": "ok",
        "text": text,
        "tier": tier,
        "division": division,
        "lp": lp,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "color": TIER_COLORS.get(tier, "#8b93a8"),
    }


def fetch_rank(display_name: str, tag_line: str, region: str, timeout: int = 12) -> dict:
    """
    Fetch solo-queue rank data for an account from op.gg.

    Returns a dict with:
        - ``status``: "ok", "unranked", or "error"
        - ``text``:   short display string, e.g. "Gold 2  45 LP  80W / 70L"
        - ``color``:  hex colour for the tier label
        - extra keys when status=="ok": tier, division, lp, wins, losses, win_rate
        - ``message``:  error description (when status=="error")
    """
    region_slug = OPGG_REGION_MAP.get(region.upper(), region.lower())
    encoded_name = quote(display_name, safe="")
    url = f"https://op.gg/lol/summoners/{region_slug}/{encoded_name}-{tag_line}"

    try:
        response = requests.get(url, headers=_HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Timeout", "color": "#585b70"}
    except requests.exceptions.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else "?"
        return {"status": "error", "message": f"HTTP {code}", "color": "#585b70"}
    except requests.exceptions.RequestException as exc:
        return {"status": "error", "message": str(exc), "color": "#585b70"}

    result = _parse_meta_description(response.text)
    if result:
        return result

    return {"status": "unranked", "text": "Unranked", "color": "#585b70"}



