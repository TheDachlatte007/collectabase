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
    platform_id: int
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


class PlatformCreate(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    type: Optional[str] = None
