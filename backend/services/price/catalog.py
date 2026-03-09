import asyncio
import re
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ...database import dict_from_row, get_db
from .utils import (
    HEADERS,
    PLATFORM_SLUGS,
    _catalog_match_score,
    _clean_catalog_title,
    _normalize_text,
    _parse_usd_price,
    _prices_differ,
    _to_eur,
)

def _lookup_local_catalog_price(title: str, platform_name: str):
    norm_title = _normalize_text(title)
    if not norm_title: return None

    norm_platform = _normalize_text(platform_name)
    title_tokens = [t for t in _clean_catalog_title(norm_title, norm_platform).split() if len(t) >= 3]

    try:
        with get_db() as db:
            rows = []
            if norm_platform:
                if title_tokens:
                    sql = "SELECT * FROM price_catalog WHERE LOWER(platform) = LOWER(?)"
                    params = [norm_platform]
                    for token in title_tokens[:3]:
                        sql += " AND LOWER(title) LIKE ?"
                        params.append(f"%{token}%")
                    sql += " ORDER BY scraped_at DESC LIMIT 2000"
                    rows = db.execute(sql, params).fetchall()
                if not rows:
                    rows = db.execute("SELECT * FROM price_catalog WHERE LOWER(platform) = LOWER(?) ORDER BY scraped_at DESC LIMIT 3000", (norm_platform,)).fetchall()
            if not rows:
                if title_tokens:
                    sql = "SELECT * FROM price_catalog WHERE 1=1"
                    params = []
                    for token in title_tokens[:3]:
                        sql += " AND LOWER(title) LIKE ?"
                        params.append(f"%{token}%")
                    sql += " ORDER BY scraped_at DESC LIMIT 4000"
                    rows = db.execute(sql, params).fetchall()
                if not rows:
                    rows = db.execute("SELECT * FROM price_catalog ORDER BY scraped_at DESC LIMIT 5000").fetchall()
    except Exception:
        return None

    best = None
    best_score = 0.0
    for row in rows:
        item = dict_from_row(row)
        row_norm_title = _normalize_text(item.get("title"))
        row_platform = _normalize_text(item.get("platform"))
        query_clean = _clean_catalog_title(norm_title, norm_platform)
        row_clean = _clean_catalog_title(row_norm_title, row_platform or norm_platform)

        score = max(
            _catalog_match_score(norm_title, row_norm_title),
            _catalog_match_score(query_clean, row_norm_title),
            _catalog_match_score(query_clean, row_clean),
        )

        if query_clean and row_clean:
            q_tokens = set(query_clean.split())
            r_tokens = set(row_clean.split())
            if q_tokens and q_tokens.issubset(r_tokens): score = max(score, 0.92)
            elif r_tokens and len(r_tokens) >= 2 and r_tokens.issubset(q_tokens): score = max(score, 0.88)

        if norm_platform and _normalize_text(item.get("platform")) == norm_platform: score += 0.10
        if score > best_score:
            best_score = score
            best = item

    if not best or best_score < 0.55: return None
    loose_eur = best.get("loose_eur")
    if loose_eur is None: return None

    return {
        "pricecharting_id": (best.get("pricecharting_id") or ""),
        "product_name": best.get("title") or title,
        "platform": best.get("platform") or platform_name,
        "loose_eur": loose_eur,
        "cib_eur": best.get("cib_eur"),
        "new_eur": best.get("new_eur"),
        "match_score": round(best_score, 3),
    }

async def _fetch_with_retry(client: httpx.AsyncClient, url: str, params: Optional[dict] = None, data: Optional[dict] = None, method: str = "GET", attempts: int = 3):
    response = None
    request_method = (method or "GET").upper()
    for attempt in range(1, attempts + 1):
        try:
            if request_method == "POST": response = await client.post(url, params=params, data=data)
            else: response = await client.get(url, params=params)
        except Exception as e:
            print(f"Catalog request error {request_method} {url} attempt={attempt}: {e}")
            if attempt < attempts:
                await asyncio.sleep(1.0 * attempt)
                continue
            return None

        if response.status_code < 400: return response
        print(f"Catalog request HTTP {response.status_code} {request_method} {url} attempt={attempt}")
        if response.status_code in (429, 500, 502, 503, 504) and attempt < attempts:
            await asyncio.sleep(1.0 * attempt)
            continue
        return response
    return response

async def scrape_platform_catalog(platform_slug: str, platform_label: str) -> list:
    entries = []
    base_url = f"https://www.pricecharting.com/console/{platform_slug}"
    previous_signature = None
    page_size_hint = None
    seen_cursors = set()
    request_method = "GET"
    request_params = {"sort": "title", "order": "asc"}
    request_data = None

    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        for page in range(1, 401):
            res = await _fetch_with_retry(client, base_url, params=request_params, data=request_data, method=request_method, attempts=3)
            if res is None or res.status_code >= 400: break

            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.select_one("table#games_table")
            if not table: break
            rows = table.select("tbody tr")
            if not rows: break

            page_entries = []
            for row in rows:
                title_cell = row.select_one("td.title a")
                if not title_cell: continue
                title = title_cell.get_text(strip=True)
                href = title_cell.get("href", "")
                pc_id_match = re.search(r"/game/[^/]+/(.+)$", href)
                pc_id = pc_id_match.group(1) if pc_id_match else ""
                page_url = f"https://www.pricecharting.com{href}" if href else ""

                def cell_price(*classes):
                    for cls in classes:
                        td = row.select_one(f"td.{cls}")
                        if not td: continue
                        span = td.select_one("span.price, span.js-price") or td
                        parsed = _parse_usd_price(span.get_text(strip=True))
                        if parsed is not None: return parsed
                    return None

                loose_usd = cell_price("used_price", "loose_price")
                cib_usd = cell_price("cib_price", "complete_price")
                new_usd = cell_price("new_price")

                if title and (loose_usd is not None or cib_usd is not None):
                    page_entries.append({
                        "pricecharting_id": pc_id,
                        "title": title,
                        "platform": platform_label,
                        "loose_usd": loose_usd,
                        "cib_usd": cib_usd,
                        "new_usd": new_usd,
                        "page_url": page_url,
                    })

            if not page_entries: break
            signature = tuple((r["pricecharting_id"] or r["title"]).strip().lower() for r in page_entries)
            if previous_signature and signature == previous_signature: break
            previous_signature = signature

            if page_size_hint is None: page_size_hint = len(page_entries)
            entries.extend(page_entries)

            next_form = soup.select_one("form.next_page.js-next-page, form.next_page")
            if not next_form: break
            next_payload = {}
            for inp in next_form.select("input[name]"):
                name = (inp.get("name") or "").strip()
                if not name: continue
                next_payload[name] = (inp.get("value") or "").strip()

            cursor = next_payload.get("cursor", "")
            if not cursor or cursor in seen_cursors: break
            seen_cursors.add(cursor)

            request_method = (next_form.get("method") or "POST").upper()
            if request_method == "GET": request_params, request_data = next_payload, None
            else: request_params, request_data = None, next_payload

            action = (next_form.get("action") or "").strip()
            if action: base_url = urljoin(base_url, action)

            if page_size_hint and len(page_entries) < max(10, page_size_hint): break
            await asyncio.sleep(1.1)

    return entries

def _upsert_catalog_entries(entries: list, eur_rate: float):
    if not entries: return {"processed": 0, "inserted": 0, "updated": 0, "unchanged": 0, "deduped_in_batch": 0, "duplicates_removed": 0}

    deduped_entries = []
    seen = set()
    deduped_in_batch = 0
    for e in entries:
        platform_key = (e.get("platform") or "").strip().lower()
        title_key = (e.get("title") or "").strip().lower()
        pc_id = (e.get("pricecharting_id") or "").strip().lower()
        key = (platform_key, pc_id if pc_id else title_key)
        if key in seen:
            deduped_in_batch += 1
            continue
        seen.add(key)
        deduped_entries.append(e)

    inserted = updated = unchanged = duplicates_removed = 0
    with get_db() as db:
        for e in deduped_entries:
            platform = e["platform"]
            title = e["title"]
            pc_id = (e.get("pricecharting_id") or "").strip()

            existing_rows = []
            if pc_id:
                existing_rows = db.execute("SELECT id, loose_usd, cib_usd, new_usd FROM price_catalog WHERE platform = ? AND pricecharting_id = ? ORDER BY id DESC", (platform, pc_id)).fetchall()
            if not existing_rows:
                existing_rows = db.execute("SELECT id, loose_usd, cib_usd, new_usd FROM price_catalog WHERE platform = ? AND LOWER(title) = LOWER(?) ORDER BY id DESC", (platform, title)).fetchall()

            keep = existing_rows[0] if existing_rows else None
            if len(existing_rows) > 1:
                dup_ids = [row["id"] for row in existing_rows[1:]]
                db.executemany("DELETE FROM price_catalog WHERE id = ?", [(d,) for d in dup_ids])
                duplicates_removed += len(dup_ids)

            loose_usd, cib_usd, new_usd = e["loose_usd"], e["cib_usd"], e["new_usd"]
            loose_eur, cib_eur, new_eur = _to_eur(loose_usd, eur_rate), _to_eur(cib_usd, eur_rate), _to_eur(new_usd, eur_rate)

            if not keep:
                db.execute(
                    "INSERT INTO price_catalog (pricecharting_id, title, platform, loose_usd, cib_usd, new_usd, loose_eur, cib_eur, new_eur, page_url, scraped_at, changed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (pc_id, title, platform, loose_usd, cib_usd, new_usd, loose_eur, cib_eur, new_eur, e["page_url"]),
                )
                inserted += 1
                continue

            prices_changed = _prices_differ(keep["loose_usd"], loose_usd) or _prices_differ(keep["cib_usd"], cib_usd) or _prices_differ(keep["new_usd"], new_usd)
            if prices_changed:
                db.execute(
                    "UPDATE price_catalog SET pricecharting_id = ?, title = ?, platform = ?, loose_usd = ?, cib_usd = ?, new_usd = ?, loose_eur = ?, cib_eur = ?, new_eur = ?, page_url = ?, scraped_at = CURRENT_TIMESTAMP, changed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (pc_id, title, platform, loose_usd, cib_usd, new_usd, loose_eur, cib_eur, new_eur, e["page_url"], keep["id"]),
                )
                updated += 1
            else:
                db.execute(
                    "UPDATE price_catalog SET pricecharting_id = ?, title = ?, platform = ?, loose_eur = ?, cib_eur = ?, new_eur = ?, page_url = ?, scraped_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (pc_id, title, platform, loose_eur, cib_eur, new_eur, e["page_url"], keep["id"]),
                )
                unchanged += 1
        db.commit()

    return {"processed": len(deduped_entries), "inserted": inserted, "updated": updated, "unchanged": unchanged, "deduped_in_batch": deduped_in_batch, "duplicates_removed": duplicates_removed}

def _platform_label_from_slug(slug: str) -> Optional[str]:
    if not slug: return None
    for label, mapped_slug in PLATFORM_SLUGS.items():
        if mapped_slug == slug: return label
    return None

def _derive_platform_label(page_url: Optional[str]) -> Optional[str]:
    if not page_url: return None
    m = re.search(r"/game/([^/]+)/", page_url)
    if not m: return None
    return _platform_label_from_slug(m.group(1))
