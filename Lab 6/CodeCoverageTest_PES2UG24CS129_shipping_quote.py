
import pytest

from shipping_quote import (
    process_shipments,
    monitor_container_pressures,
)


# --------------------------------------------------
# PROCESS SHIPMENTS - VALIDATION TESTS
# --------------------------------------------------

def test_invalid_shipments_input():
    with pytest.raises(ValueError):
        process_shipments("invalid", 10.0)


def test_negative_handling_fee():
    with pytest.raises(ValueError):
        process_shipments([], -5.0)


def test_empty_shipments():
    result = process_shipments([], 10.0)

    assert result == {
        "total_quote": 0.0,
        "status": "NO_CARGO"
    }


# --------------------------------------------------
# MANIFEST AND TRANSPORT MODE TESTS
# --------------------------------------------------

def test_unapproved_manifest():
    shipments = [
        {"manifest_approved": False, "mode": "air"}
    ]

    result = process_shipments(shipments, 10.0)

    assert result["status"] == "NO_CARGO"


def test_default_shipment_values():
    shipments = [
        {"manifest_approved": True}
    ]

    result = process_shipments(shipments, 10.0)

    assert result == {
        "total_quote": 10.0,
        "status": "CLEARED"
    }


def test_air_shipment():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "air",
            "packages": [
                {"weight_kg": 2, "is_hazmat": False}
            ]
        }
    ]

    result = process_shipments(shipments, 5.0)

    assert result["total_quote"] == 29.0
    assert result["status"] == "CLEARED"


def test_invalid_transport_mode():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "sea",
            "packages": []
        }
    ]

    result = process_shipments(shipments, 10.0)

    assert result["status"] == "NO_CARGO"


# --------------------------------------------------
# PACKAGE VALIDATION AND PRICING TESTS
# --------------------------------------------------

def test_zero_weight_package():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": 0}
            ]
        }
    ]

    result = process_shipments(shipments, 10.0)

    assert result == {
        "total_quote": 10.0,
        "status": "CLEARED"
    }

def test_negative_weight_package():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": -5}
            ]
        }
    ]

    result = process_shipments(shipments, 10.0)

    assert result == {
        "total_quote": 10.0,
        "status": "CLEARED"
    }


def test_normal_ground_package():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": 10, "is_hazmat": False}
            ]
        }
    ]

    result = process_shipments(shipments, 20.0)

    assert result["total_quote"] == 60.0
    assert result["status"] == "CLEARED"


def test_heavy_package():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": 40, "is_hazmat": False}
            ]
        }
    ]

    result = process_shipments(shipments, 20.0)

    assert result["total_quote"] == 260.0
    assert result["status"] == "CLEARED"


def test_hazmat_non_fragile_package():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": False,
            "packages": [
                {"weight_kg": 5, "is_hazmat": True}
            ]
        }
    ]

    result = process_shipments(shipments, 10.0)

    assert result["total_quote"] == 60.0
    assert result["status"] == "CLEARED"


def test_hazmat_fragile_package():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": True,
            "packages": [
                {"weight_kg": 5, "is_hazmat": True}
            ]
        }
    ]

    result = process_shipments(shipments, 10.0)

    assert result == {
        "total_quote": 0.0,
        "status": "NO_CARGO"
    }


def test_express_priority():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "express_priority": True,
            "packages": [
                {"weight_kg": 10, "is_hazmat": False}
            ]
        }
    ]

    result = process_shipments(shipments, 20.0)

    assert result["total_quote"] == 75.0
    assert result["status"] == "CLEARED"


def test_flagged_review():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": 0},
                {"weight_kg": -1},
                {"weight_kg": 0},
                {"weight_kg": -2}
            ]
        }
    ]

    result = process_shipments(shipments, 10.0)

    assert result == {
        "total_quote": 10.0,
        "status": "FLAGGED_REVIEW"
    }


# --------------------------------------------------
# CONTAINER PRESSURE MONITORING TESTS
# --------------------------------------------------

def test_empty_pressure_logs():
    result = monitor_container_pressures([])

    assert result == "NO_DATA"


def test_stable_pressure():
    pressure_logs = [
        [15.0, 16.0, 14.0, 15.5]
    ]

    result = monitor_container_pressures(pressure_logs)

    assert result == "STABLE"


def test_single_low_pressure():
    pressure_logs = [
        [15.0, 13.0, 15.0]
    ]

    result = monitor_container_pressures(pressure_logs)

    assert result == "STABLE"


def test_pressure_recovery_resets_streak():
    pressure_logs = [
        [13.0, 15.0, 13.0, 15.0]
    ]

    result = monitor_container_pressures(pressure_logs)

    assert result == "STABLE"


def test_leak_detected():
    pressure_logs = [
        [15.0, 13.0, 12.0]
    ]

    result = monitor_container_pressures(pressure_logs)

    assert result == "LEAK_DETECTED"


def test_leak_in_multiple_containers():
    pressure_logs = [
        [15.0, 14.0],
        [13.0, 12.0]
    ]

    result = monitor_container_pressures(pressure_logs)

    assert result == "LEAK_DETECTED"
