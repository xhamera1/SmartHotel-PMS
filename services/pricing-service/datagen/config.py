"""Pydantic models for the synthetic datagen YAML config (Appendix C)."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

EventCategory = Literal["MUSIC", "SPORTS", "CONFERENCE", "CULTURE"]


class HorizonConfig(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def start_before_end(self) -> Self:
        if self.end < self.start:
            msg = f"horizon.end ({self.end}) must be on or after horizon.start ({self.start})"
            raise ValueError(msg)
        return self


class LocationConfig(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class RoomTypeConfig(BaseModel):
    code: Annotated[str, Field(min_length=1, max_length=30)]
    rooms: Annotated[int, Field(gt=0)]
    base_price: Annotated[float, Field(gt=0)]
    min_price: Annotated[float, Field(gt=0)]
    max_price: Annotated[float, Field(gt=0)]
    elasticity: Annotated[float, Field(gt=0)]

    @model_validator(mode="after")
    def price_band(self) -> Self:
        if not (self.min_price <= self.base_price <= self.max_price):
            msg = (
                f"room type {self.code}: require min_price ≤ base_price ≤ max_price "
                f"({self.min_price}, {self.base_price}, {self.max_price})"
            )
            raise ValueError(msg)
        return self


class HotelConfig(BaseModel):
    city: Annotated[str, Field(min_length=1)]
    location: LocationConfig
    room_types: Annotated[list[RoomTypeConfig], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_codes(self) -> Self:
        codes = [rt.code for rt in self.room_types]
        if len(codes) != len(set(codes)):
            msg = f"duplicate room type codes: {codes}"
            raise ValueError(msg)
        return self


class DemandConfig(BaseModel):
    """Weekday multipliers are Mon..Sun (index 0 = Monday)."""

    weekday_multipliers: Annotated[list[float], Field(min_length=7, max_length=7)]
    season_amplitude: Annotated[float, Field(ge=0, le=1)]
    holiday_boost: Annotated[float, Field(ge=0)]
    noise_sigma: Annotated[float, Field(ge=0)]
    latent_shock_sigma: Annotated[float, Field(ge=0)]

    @field_validator("weekday_multipliers")
    @classmethod
    def positive_weekdays(cls, value: list[float]) -> list[float]:
        if any(v <= 0 for v in value):
            raise ValueError("weekday_multipliers must be strictly positive")
        return value


class CategoryProfile(BaseModel):
    share: Annotated[float, Field(gt=0, le=1)]
    attendance: Annotated[list[int], Field(min_length=2, max_length=2)]
    uplift_per_10k: Annotated[float, Field(ge=0)]

    @field_validator("attendance")
    @classmethod
    def attendance_range(cls, value: list[int]) -> list[int]:
        low, high = value
        if low <= 0 or high < low:
            raise ValueError("attendance must be [low, high] with 0 < low ≤ high")
        return value


class EventsConfig(BaseModel):
    per_year: Annotated[int, Field(gt=0)]
    categories: dict[EventCategory, CategoryProfile]

    @model_validator(mode="after")
    def shares_sum_to_one(self) -> Self:
        total = sum(profile.share for profile in self.categories.values())
        if abs(total - 1.0) > 1e-6:
            msg = f"event category shares must sum to 1.0 (got {total})"
            raise ValueError(msg)
        return self


class LeadTimeGammaConfig(BaseModel):
    shape: Annotated[float, Field(gt=0)]
    scale: Annotated[float, Field(gt=0)]


class BookingConfig(BaseModel):
    lead_time_gamma: LeadTimeGammaConfig
    cancellation_rate: Annotated[float, Field(ge=0, lt=1)]


class SnapshotsConfig(BaseModel):
    lead_times_days: Annotated[list[int], Field(min_length=1)]

    @field_validator("lead_times_days")
    @classmethod
    def positive_lead_times(cls, value: list[int]) -> list[int]:
        if any(v <= 0 for v in value):
            raise ValueError("lead_times_days must be positive integers")
        if len(value) != len(set(value)):
            raise ValueError("lead_times_days must be unique")
        return value


class DatagenConfig(BaseModel):
    """Top-level generator configuration — Appendix C schema."""

    seed: Annotated[int, Field(ge=0)]
    horizon: HorizonConfig
    hotel: HotelConfig
    demand: DemandConfig
    events: EventsConfig
    booking: BookingConfig
    snapshots: SnapshotsConfig

    @classmethod
    def from_yaml(cls, path: Path | str) -> Self:
        config_path = Path(path)
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            msg = f"config root must be a mapping, got {type(raw).__name__}"
            raise ValueError(msg)
        return cls.model_validate(raw)

    def canonical_bytes(self) -> bytes:
        """Stable UTF-8 JSON used for config hashing (sorted keys, no whitespace noise)."""
        return self.model_dump_json(indent=None).encode("utf-8")

    def config_hash(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()
