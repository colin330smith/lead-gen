from __future__ import annotations

from datetime import datetime

from backend.models.property import TCADFeature, bulk_properties_from_features


def test_bulk_properties_parses_feature() -> None:
    feature = {
        "attributes": {
            "PROP_ID": 123,
            "geo_id": "0123456789",
            "py_owner_name": "  DOE FAMILY TRUST ",
            "py_address": "PO BOX 123",
            "situs_address": "123 MAIN ST AUSTIN TX 78701",
            "situs_zip": "78701",
            "land_type_desc": "SINGLE FAMILY RESIDENCE",
            "land_state_cd": "A",
            "entities": " 03 04 ",
            "legal_desc": "LOT 1 BLOCK A SAMPLE SUBD",
            "deed_num": "20230101",
            "deed_book_id": "1234",
            "deed_book_page": "56",
            "deed_date": int(datetime(2023, 1, 1).timestamp() * 1000),
            "market_value": 450000,
            "appraised_val": 430000,
            "assessed_val": 350000,
            "imprv_homesite_val": 320000,
            "imprv_non_homesite_val": 10000,
            "land_homesite_val": 110000,
            "land_non_homesite_val": "0",
            "tcad_acres": 0.25,
            "GIS_acres": 0.24,
            "situs_num": "123",
            "situs_street": "MAIN",
            "situs_street_prefx": "N",
            "situs_street_suffix": "ST",
            "situs_city": "AUSTIN",
            "F1year_imprv": 1999,
            "py_owner_id": 5555,
            "CENTROID_X": 3123456.0,
            "CENTROID_Y": 10123456.0,
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    }

    properties = bulk_properties_from_features([feature])
    assert len(properties) == 1
    prop = properties[0]

    assert prop.prop_id == 123
    assert prop.owner_name == "DOE FAMILY TRUST"
    assert prop.deed_date == datetime(2023, 1, 1).date()
    record = prop.to_record()
    assert record["prop_id"] == 123
    assert record["geometry"] == feature["geometry"]


def test_tcad_feature_handles_blank_strings() -> None:
    feature = TCADFeature.model_validate(
        {
            "attributes": {
                "PROP_ID": 1,
                "py_owner_name": " ",
                "py_address": None,
            }
        }
    )

    assert feature.attributes.py_owner_name is None
