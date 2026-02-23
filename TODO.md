# TODO

## Open items

- [x] Cache external console/accessory image URLs locally (or serve via backend proxy) to avoid broken hotlinks from third-party hosts.
- [x] Simplify `GameDetail` action bar UX: keep primary actions visible, move external links (`eBay`, `PriceCharting`, `RAWG`) into a compact `More` menu.
- [x] Add backend tests for local `price_catalog` matching in `fetch-market-price` (good match, weak match rejection, platform-aware matching).
