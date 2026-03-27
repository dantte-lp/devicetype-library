"""Fetch and adapt YAML device types from upstream - v2: keep slugs."""

from pathlib import Path
import requests

UPSTREAM_API = "https://api.github.com/repos/netbox-community/devicetype-library/contents/device-types/{manufacturer}"
UPSTREAM_RAW = "https://raw.githubusercontent.com/netbox-community/devicetype-library/master/device-types/{manufacturer}/{filename}"


def adapt_yaml_content_v2(content: str) -> str:
    """Only remove mgmt_only: false. Keep everything else from upstream."""
    lines = content.splitlines()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped == "mgmt_only: false":
            continue
        result.append(line)
    out = "\n".join(result)
    if not out.endswith("\n"):
        out += "\n"
    return out


def full_sync(manufacturer: str, local_dir: Path) -> dict:
    """Re-download ALL models from upstream, overwriting local. Returns stats."""
    url = UPSTREAM_API.format(manufacturer=manufacturer)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    upstream_files = [f["name"] for f in resp.json() if f["name"].endswith((".yaml", ".yml"))]

    stats = {"created": 0, "updated": 0, "total": len(upstream_files)}
    for filename in upstream_files:
        raw_url = UPSTREAM_RAW.format(manufacturer=manufacturer, filename=filename)
        content = requests.get(raw_url, timeout=30).text
        adapted = adapt_yaml_content_v2(content)
        
        target = local_dir / filename
        existed = target.exists()
        target.write_text(adapted)
        
        if existed:
            stats["updated"] += 1
        else:
            stats["created"] += 1
    return stats
