"""User-supplied observations, with clocks and units kept separate from model marks."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from urllib.parse import urlparse


@dataclass(frozen=True)
class Quote:
    instrument: str
    kind: str
    observed_at: datetime
    retrieved_at: datetime
    source_url: str
    unit: str
    currency: str
    bid: float | None = None
    ask: float | None = None
    nav: float | None = None
    delayed: bool = True

    def __post_init__(self):
        if self.kind not in {"bid_ask","nav"} or not self.instrument.strip(): raise ValueError("Invalid quote identity/type")
        if self.unit != "USD_per_ETF_share" or self.currency != "USD": raise ValueError("Require explicit ETF-share USD units")
        for clock in [self.observed_at,self.retrieved_at]:
            if clock.tzinfo is None or clock.utcoffset() is None: raise ValueError("Timezone-aware clocks required")
        if self.observed_at > self.retrieved_at: raise ValueError("Quote observed after retrieval")
        if urlparse(self.source_url).scheme != "https" or not urlparse(self.source_url).netloc:
            raise ValueError("Public HTTPS source required")
        values=[v for v in [self.bid,self.ask,self.nav] if v is not None]
        if any(not isfinite(v) or v <= 0 for v in values): raise ValueError("Invalid quote value")
        if self.kind == "bid_ask" and (self.bid is None or self.ask is None or self.nav is not None or self.bid > self.ask):
            raise ValueError("Require uncrossed bid/ask, no NAV")
        if self.kind == "nav" and (self.nav is None or self.bid is not None or self.ask is not None):
            raise ValueError("NAV is a separate observation")

    def summary(self, as_of: datetime, max_age_seconds=300):
        if as_of.tzinfo is None or as_of.utcoffset() is None: raise ValueError("Aware evaluation time required")
        age=(as_of-self.observed_at).total_seconds()
        if not isfinite(max_age_seconds) or max_age_seconds < 0 or age < 0: raise ValueError("Invalid evaluation time")
        # Even an on-time displayed quote does not establish executable size/fill.
        return {"instrument":self.instrument,"kind":self.kind,"age_seconds":age,
                "time_aligned":age <= max_age_seconds,"delayed":self.delayed,
                "execution_proven":False,
                "midpoint":(self.bid+self.ask)/2 if self.kind == "bid_ask" else None,
                "nav":self.nav,"unit":self.unit,
                "spread_bps":10000*(self.ask-self.bid)/((self.ask+self.bid)/2) if self.kind == "bid_ask" else None}


def read_quotes(path):
    required={"instrument","kind","observed_at","retrieved_at","source_url","unit","currency","bid","ask","nav","delayed"}
    with open(path,encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        if set(reader.fieldnames or []) != required: raise ValueError("Quote CSV schema mismatch")
        rows=[]
        for row in reader:
            if row["delayed"] not in {"true","false"}: raise ValueError("delayed must be true/false")
            rows.append(Quote(**{k:datetime.fromisoformat(v) if k in {"observed_at","retrieved_at"}
                else float(v) if k in {"bid","ask","nav"} and v else None if k in {"bid","ask","nav"}
                else v == "true" if k == "delayed" else v for k,v in row.items()}))
    return rows
