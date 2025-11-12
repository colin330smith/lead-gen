from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import BigInteger, Date, Float, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _normalize_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class TCADAttributes(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    prop_id: int = Field(alias="PROP_ID")
    geo_id: str | None = Field(default=None, alias="geo_id")
    py_owner_name: str | None = Field(default=None, alias="py_owner_name")
    py_address: str | None = Field(default=None, alias="py_address")
    situs_address: str | None = Field(default=None, alias="situs_address")
    situs_zip: str | None = Field(default=None, alias="situs_zip")
    land_type_desc: str | None = Field(default=None, alias="land_type_desc")
    land_state_cd: str | None = Field(default=None, alias="land_state_cd")
    entities: str | None = Field(default=None, alias="entities")
    legal_desc: str | None = Field(default=None, alias="legal_desc")
    deed_num: str | None = Field(default=None, alias="deed_num")
    deed_book_id: str | None = Field(default=None, alias="deed_book_id")
    deed_book_page: str | None = Field(default=None, alias="deed_book_page")
    deed_date: datetime | None = Field(default=None, alias="deed_date")

    market_value: int | None = Field(default=None, alias="market_value")
    appraised_val: int | None = Field(default=None, alias="appraised_val")
    assessed_val: int | None = Field(default=None, alias="assessed_val")
    imprv_homesite_val: int | None = Field(default=None, alias="imprv_homesite_val")
    imprv_non_homesite_val: int | None = Field(default=None, alias="imprv_non_homesite_val")
    land_homesite_val: int | None = Field(default=None, alias="land_homesite_val")
    land_non_homesite_val: str | None = Field(default=None, alias="land_non_homesite_val")

    tcad_acres: float | None = Field(default=None, alias="tcad_acres")
    gis_acres: float | None = Field(default=None, alias="GIS_acres")

    situs_num: str | None = Field(default=None, alias="situs_num")
    situs_street: str | None = Field(default=None, alias="situs_street")
    situs_street_prefx: str | None = Field(default=None, alias="situs_street_prefx")
    situs_street_suffix: str | None = Field(default=None, alias="situs_street_suffix")
    situs_city: str | None = Field(default=None, alias="situs_city")

    f1year_imprv: int | None = Field(default=None, alias="F1year_imprv")
    centroid_x: float | None = Field(default=None, alias="CENTROID_X")
    centroid_y: float | None = Field(default=None, alias="CENTROID_Y")
    py_owner_id: int | None = Field(default=None, alias="py_owner_id")

    @field_validator(
        "py_owner_name",
        "py_address",
        "situs_address",
        "situs_zip",
        "land_type_desc",
        "land_state_cd",
        "entities",
        "legal_desc",
        "deed_num",
        "deed_book_id",
        "deed_book_page",
        "land_non_homesite_val",
        "situs_num",
        "situs_street",
        "situs_street_prefx",
        "situs_street_suffix",
        "situs_city",
        mode="before",
    )
    def _strip_strings(cls, value: Any) -> Any:  # noqa: N805 - Pydantic validator signature
        if isinstance(value, str):
            return _normalize_str(value)
        return value

    @field_validator("deed_date", mode="before")
    def _parse_deed_date(cls, value: Any) -> Any:  # noqa: N805
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            # ArcGIS returns epoch milliseconds
            return datetime.utcfromtimestamp(value / 1000)
        return value


class TCADFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")

    attributes: TCADAttributes
    geometry: dict[str, Any] | None = None


class Property(Base):
    __tablename__ = "properties"

    prop_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    geo_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    owner_address: Mapped[str | None] = mapped_column(String(150), nullable=True)
    situs_address: Mapped[str | None] = mapped_column(String(150), nullable=True)
    situs_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)
    land_type_desc: Mapped[str | None] = mapped_column(String(50), nullable=True)
    land_state_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    entities: Mapped[str | None] = mapped_column(String(150), nullable=True)
    legal_description: Mapped[str | None] = mapped_column(String(400), nullable=True)

    deed_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deed_book_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deed_book_page: Mapped[str | None] = mapped_column(String(20), nullable=True)
    deed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    market_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    appraised_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    assessed_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    improvement_homesite_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    improvement_non_homesite_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    land_homesite_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    land_non_homesite_value: Mapped[str | None] = mapped_column(String(50), nullable=True)

    tcad_acres: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    gis_acres: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)

    situs_num: Mapped[str | None] = mapped_column(String(50), nullable=True)
    situs_street: Mapped[str | None] = mapped_column(String(100), nullable=True)
    situs_street_prefx: Mapped[str | None] = mapped_column(String(10), nullable=True)
    situs_street_suffix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    situs_city: Mapped[str | None] = mapped_column(String(250), nullable=True)

    first_improvement_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    centroid_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    geometry: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    @classmethod
    def from_feature(cls, feature: TCADFeature) -> "Property":
        data = feature.attributes
        return cls(
            prop_id=data.prop_id,
            geo_id=data.geo_id,
            owner_name=data.py_owner_name,
            owner_address=data.py_address,
            situs_address=data.situs_address,
            situs_zip=data.situs_zip,
            land_type_desc=data.land_type_desc,
            land_state_code=data.land_state_cd,
            entities=data.entities,
            legal_description=data.legal_desc,
            deed_number=data.deed_num,
            deed_book_id=data.deed_book_id,
            deed_book_page=data.deed_book_page,
            deed_date=data.deed_date.date() if isinstance(data.deed_date, datetime) else data.deed_date,
            market_value=data.market_value,
            appraised_value=data.appraised_val,
            assessed_value=data.assessed_val,
            improvement_homesite_value=data.imprv_homesite_val,
            improvement_non_homesite_value=data.imprv_non_homesite_val,
            land_homesite_value=data.land_homesite_val,
            land_non_homesite_value=data.land_non_homesite_val,
            tcad_acres=data.tcad_acres,
            gis_acres=data.gis_acres,
            situs_num=data.situs_num,
            situs_street=data.situs_street,
            situs_street_prefx=data.situs_street_prefx,
            situs_street_suffix=data.situs_street_suffix,
            situs_city=data.situs_city,
            first_improvement_year=data.f1year_imprv,
            owner_id=data.py_owner_id,
            centroid_x=data.centroid_x,
            centroid_y=data.centroid_y,
            geometry=feature.geometry,
            raw_payload=feature.model_dump(mode="json"),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "prop_id": self.prop_id,
            "geo_id": self.geo_id,
            "owner_name": self.owner_name,
            "owner_address": self.owner_address,
            "situs_address": self.situs_address,
            "situs_zip": self.situs_zip,
            "land_type_desc": self.land_type_desc,
            "land_state_code": self.land_state_code,
            "entities": self.entities,
            "legal_description": self.legal_description,
            "deed_number": self.deed_number,
            "deed_book_id": self.deed_book_id,
            "deed_book_page": self.deed_book_page,
            "deed_date": self.deed_date,
            "market_value": self.market_value,
            "appraised_value": self.appraised_value,
            "assessed_value": self.assessed_value,
            "improvement_homesite_value": self.improvement_homesite_value,
            "improvement_non_homesite_value": self.improvement_non_homesite_value,
            "land_homesite_value": self.land_homesite_value,
            "land_non_homesite_value": self.land_non_homesite_value,
            "tcad_acres": self.tcad_acres,
            "gis_acres": self.gis_acres,
            "situs_num": self.situs_num,
            "situs_street": self.situs_street,
            "situs_street_prefx": self.situs_street_prefx,
            "situs_street_suffix": self.situs_street_suffix,
            "situs_city": self.situs_city,
            "first_improvement_year": self.first_improvement_year,
            "owner_id": self.owner_id,
            "centroid_x": self.centroid_x,
            "centroid_y": self.centroid_y,
            "geometry": self.geometry,
            "raw_payload": self.raw_payload,
        }



def bulk_properties_from_features(features: Iterable[dict[str, Any]]) -> list[Property]:
    """Convert iterable of raw ArcGIS features into Property ORM objects."""

    parsed: list[Property] = []
    for feature in features:
        tcad_feature = TCADFeature.model_validate(feature)
        parsed.append(Property.from_feature(tcad_feature))
    return parsed


__all__ = ["Property", "TCADFeature", "TCADAttributes", "bulk_properties_from_features"]
