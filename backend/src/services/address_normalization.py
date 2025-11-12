"""Address normalization and matching service."""

from __future__ import annotations

import re
from typing import Any

from ..utils.logging import get_logger

_logger = get_logger(component="address_normalization")

# Common street suffix mappings
STREET_SUFFIXES = {
    "st": "street",
    "st.": "street",
    "ave": "avenue",
    "ave.": "avenue",
    "av": "avenue",
    "av.": "avenue",
    "rd": "road",
    "rd.": "road",
    "dr": "drive",
    "dr.": "drive",
    "ln": "lane",
    "ln.": "lane",
    "blvd": "boulevard",
    "blvd.": "boulevard",
    "ct": "court",
    "ct.": "court",
    "pl": "place",
    "pl.": "place",
    "cir": "circle",
    "cir.": "circle",
    "pkwy": "parkway",
    "pkwy.": "parkway",
    "trl": "trail",
    "trl.": "trail",
    "way": "way",
}

# Common street prefix mappings
STREET_PREFIXES = {
    "n": "north",
    "n.": "north",
    "s": "south",
    "s.": "south",
    "e": "east",
    "e.": "east",
    "w": "west",
    "w.": "west",
}


def normalize_address(address: str | None) -> dict[str, Any]:
    """
    Normalize an address string into components.
    
    Returns:
        Dictionary with keys: street_number, street_name, street_suffix, 
        street_prefix, city, state, zip_code, normalized
    """
    if not address:
        return {
            "street_number": None,
            "street_name": None,
            "street_suffix": None,
            "street_prefix": None,
            "city": None,
            "state": None,
            "zip_code": None,
            "normalized": "",
        }
    
    # Clean the address
    address = address.strip().upper()
    
    # Remove extra whitespace
    address = re.sub(r"\s+", " ", address)
    
    # Extract components
    result = {
        "street_number": None,
        "street_name": None,
        "street_suffix": None,
        "street_prefix": None,
        "city": None,
        "state": None,
        "zip_code": None,
        "normalized": "",
    }
    
    # Extract ZIP code (5 digits, possibly with -4 extension)
    zip_match = re.search(r"\b(\d{5})(?:-(\d{4}))?\b", address)
    if zip_match:
        result["zip_code"] = zip_match.group(1)
        address = address[: zip_match.start()].strip()
    
    # Extract state (2-letter code, usually at end before ZIP)
    state_match = re.search(r"\b([A-Z]{2})\b", address)
    if state_match and state_match.group(1) in ["TX", "CA", "NY", "FL", "IL"]:  # Common states
        result["state"] = state_match.group(1)
        address = address[: state_match.start()].strip()
    
    # Extract city (usually before state, may contain multiple words)
    # This is heuristic - may need refinement
    if result["state"]:
        parts = address.rsplit(",", 1)
        if len(parts) == 2:
            result["city"] = parts[1].strip()
            address = parts[0].strip()
        else:
            # Try to extract city from end
            city_match = re.search(r"([A-Z][A-Z\s]+),?\s*$", address)
            if city_match:
                potential_city = city_match.group(1).strip()
                if len(potential_city.split()) <= 3:  # Reasonable city name length
                    result["city"] = potential_city
                    address = address[: city_match.start()].strip()
    
    # Extract street number (digits at start)
    street_num_match = re.match(r"^(\d+[A-Z]?)\s+", address)
    if street_num_match:
        result["street_number"] = street_num_match.group(1)
        address = address[len(street_num_match.group(0)) :].strip()
    
    # Extract street prefix (N, S, E, W at start of street name)
    prefix_match = re.match(r"^([NSEW]\.?)\s+", address)
    if prefix_match:
        prefix = prefix_match.group(1).lower().rstrip(".")
        result["street_prefix"] = STREET_PREFIXES.get(prefix, prefix)
        address = address[len(prefix_match.group(0)) :].strip()
    
    # Extract street suffix (at end of street name)
    # Check for common suffixes
    address_lower = address.lower()
    for suffix_abbr, suffix_full in STREET_SUFFIXES.items():
        if address_lower.endswith(" " + suffix_abbr) or address_lower.endswith(" " + suffix_full):
            result["street_suffix"] = suffix_full
            # Remove suffix from address
            suffix_pattern = r"\s+" + re.escape(suffix_abbr) + r"\.?$"
            address = re.sub(suffix_pattern, "", address, flags=re.IGNORECASE)
            suffix_pattern = r"\s+" + re.escape(suffix_full) + r"$"
            address = re.sub(suffix_pattern, "", address, flags=re.IGNORECASE)
            break
    
    # Remaining address is street name
    result["street_name"] = address.strip() if address else None
    
    # Build normalized address
    normalized_parts = []
    if result["street_number"]:
        normalized_parts.append(result["street_number"])
    if result["street_prefix"]:
        normalized_parts.append(result["street_prefix"].title())
    if result["street_name"]:
        normalized_parts.append(result["street_name"].title())
    if result["street_suffix"]:
        normalized_parts.append(result["street_suffix"].title())
    
    result["normalized"] = " ".join(normalized_parts) if normalized_parts else ""
    
    return result


def normalize_address_simple(address: str | None) -> str:
    """Simple address normalization - just clean and standardize."""
    if not address:
        return ""
    
    # Clean
    address = address.strip().upper()
    address = re.sub(r"\s+", " ", address)
    
    # Normalize common abbreviations
    for abbr, full in STREET_SUFFIXES.items():
        address = re.sub(rf"\b{re.escape(abbr)}\b\.?", full, address, flags=re.IGNORECASE)
    
    for abbr, full in STREET_PREFIXES.items():
        address = re.sub(rf"\b{re.escape(abbr)}\b\.?", full, address, flags=re.IGNORECASE)
    
    return address


def address_similarity(addr1: str, addr2: str) -> float:
    """
    Calculate similarity between two addresses (0.0 to 1.0).
    
    Uses simple token-based matching. For production, consider using
    fuzzy string matching libraries like rapidfuzz or python-Levenshtein.
    """
    if not addr1 or not addr2:
        return 0.0
    
    # Normalize both addresses
    norm1 = normalize_address_simple(addr1).lower()
    norm2 = normalize_address_simple(addr2).lower()
    
    if norm1 == norm2:
        return 1.0
    
    # Token-based similarity
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    # Jaccard similarity
    similarity = len(intersection) / len(union) if union else 0.0
    
    return similarity

