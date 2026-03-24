from typing import Optional

from pydantic import BaseModel


class TitleSearch(BaseModel):
    title: str

class IGDBSearch(TitleSearch):
    pass


class BarcodeLookup(BaseModel):
    barcode: str


class GameCreate(BaseModel):
    title: str
    platform_id: Optional[int] = None
    item_type: Optional[str] = "game"
    quantity: Optional[int] = 1
    barcode: Optional[str] = None
    igdb_id: Optional[int] = None
    comicvine_id: Optional[str] = None
    hobbydb_id: Optional[str] = None
    mfc_id: Optional[str] = None
    release_date: Optional[str] = None
    publisher: Optional[str] = None
    developer: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    region: Optional[str] = None
    condition: Optional[str] = None
    completeness: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None
    is_wishlist: bool = False
    wishlist_max_price: Optional[float] = None
    character_name: Optional[str] = None
    series_name: Optional[str] = None
    scale: Optional[str] = None
    funko_number: Optional[str] = None
    vinyl_format: Optional[str] = None


class GameUpdate(GameCreate):
    title: Optional[str] = None
    platform_id: Optional[int] = None
    item_type: Optional[str] = None
    quantity: Optional[int] = None
    barcode: Optional[str] = None
    igdb_id: Optional[int] = None
    comicvine_id: Optional[str] = None
    hobbydb_id: Optional[str] = None
    mfc_id: Optional[str] = None
    release_date: Optional[str] = None
    publisher: Optional[str] = None
    developer: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    region: Optional[str] = None
    condition: Optional[str] = None
    completeness: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None
    is_wishlist: Optional[bool] = None
    wishlist_max_price: Optional[float] = None
    character_name: Optional[str] = None
    series_name: Optional[str] = None
    scale: Optional[str] = None
    funko_number: Optional[str] = None
    vinyl_format: Optional[str] = None


class PlatformCreate(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    type: Optional[str] = None


class LotCreate(BaseModel):
    name: str
    purchase_date: Optional[str] = None
    seller: Optional[str] = None
    purchase_price_gross: Optional[float] = 0
    shipping_in: Optional[float] = 0
    fees_in: Optional[float] = 0
    other_costs: Optional[float] = 0
    notes: Optional[str] = None


class LotUpdate(BaseModel):
    name: Optional[str] = None
    purchase_date: Optional[str] = None
    seller: Optional[str] = None
    purchase_price_gross: Optional[float] = None
    shipping_in: Optional[float] = None
    fees_in: Optional[float] = None
    other_costs: Optional[float] = None
    notes: Optional[str] = None


class LotItemCreate(BaseModel):
    game_id: Optional[int] = None
    title_snapshot: Optional[str] = None
    platform_snapshot: Optional[str] = None
    item_type_snapshot: Optional[str] = None
    estimated_value: Optional[float] = None
    cost_basis_override: Optional[float] = None
    status: Optional[str] = "inventory"
    notes: Optional[str] = None


class LotItemUpdate(BaseModel):
    game_id: Optional[int] = None
    unlink_game: bool = False
    title_snapshot: Optional[str] = None
    platform_snapshot: Optional[str] = None
    item_type_snapshot: Optional[str] = None
    estimated_value: Optional[float] = None
    cost_basis_override: Optional[float] = None
    clear_cost_basis_override: bool = False
    status: Optional[str] = None
    notes: Optional[str] = None


class LotSaleUpsert(BaseModel):
    sold_at: Optional[str] = None
    channel: Optional[str] = None
    sale_price_gross: Optional[float] = 0
    platform_fees: Optional[float] = 0
    shipping_out: Optional[float] = 0
    other_costs: Optional[float] = 0
    notes: Optional[str] = None
