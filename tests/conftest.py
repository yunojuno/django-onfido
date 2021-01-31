"""Shared pytest fixtures and test data."""
import copy
import uuid

import pytest
from django.contrib.auth import get_user_model

from onfido.models import Applicant, Check, Event, Report

APPLICANT_ID = str(uuid.uuid4())
CHECK_ID = str(uuid.uuid4())
IDENTITY_REPORT_ID = str(uuid.uuid4())
DOCUMENT_REPORT_ID = str(uuid.uuid4())
DOCUMENT_ID = str(uuid.uuid4())

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        "fred", first_name="Fred", last_name="Flinstone", email="fred@example.com"
    )


@pytest.fixture
def applicant(user):
    data = copy.deepcopy(TEST_APPLICANT)
    return Applicant.objects.create_applicant(user=user, raw=data)


@pytest.fixture
def check(applicant):
    data = copy.deepcopy(TEST_CHECK)
    return Check.objects.create_check(applicant, raw=data)


@pytest.fixture
def identity_report(check):
    data = copy.deepcopy(TEST_REPORT_IDENTITY_ENHANCED)
    return Report.objects.create_report(check, raw=data)


@pytest.fixture
def document_report(check):
    data = copy.deepcopy(TEST_REPORT_DOCUMENT)
    return Report.objects.create_report(check, raw=data)


@pytest.fixture
def report(identity_report):
    return identity_report


@pytest.fixture
def event(check):
    data = copy.deepcopy(TEST_EVENT)
    return Event().parse(data)


# Test data taken from Onfido v3 API docs.

# https://documentation.onfido.com/#applicant-object
TEST_APPLICANT = {
    "id": APPLICANT_ID,
    "created_at": "2019-10-09T16:52:42Z",
    "sandbox": True,
    "first_name": "Jane",
    "last_name": "Doe",
    "email": None,
    "dob": "1990-01-01",
    "delete_at": None,
    "href": f"/v3/applicants/{APPLICANT_ID}",
    "id_numbers": [],
    "address": {
        "flat_number": None,
        "building_number": None,
        "building_name": None,
        "street": "Second Street",
        "sub_street": None,
        "town": "London",
        "state": None,
        "postcode": "S2 2DF",
        "country": "GBR",
        "line1": None,
        "line2": None,
        "line3": None,
    },
}

# https://documentation.onfido.com/#check-object
TEST_CHECK = {
    "id": CHECK_ID,
    "created_at": "2019-10-09T17:01:59Z",
    "status": "in_progress",
    "redirect_uri": None,
    "result": None,
    "sandbox": True,
    "tags": [],
    "results_uri": f"https://onfido.com/checks/{CHECK_ID}/reports",
    "form_uri": None,
    "paused": False,
    "version": "3.0",
    "report_ids": [IDENTITY_REPORT_ID],
    "href": f"/v3/checks/{CHECK_ID}",
    "applicant_id": APPLICANT_ID,
    "applicant_provides_data": False,
}

# https://documentation.onfido.com/#identity-enhanced-report
TEST_REPORT_IDENTITY_ENHANCED = {
    "created_at": "2019-10-03T15:54:20Z",
    "href": f"/v3/reports/{IDENTITY_REPORT_ID}",
    "id": IDENTITY_REPORT_ID,
    "name": "identity_enhanced",
    "properties": {
        "matched_address": 19099121,
        "matched_addresses": [
            {"id": 19099121, "match_types": ["credit_agencies", "voting_register"]}
        ],
    },
    "result": "clear",
    "status": "complete",
    "sub_result": None,
    "breakdown": {
        "sources": {
            "result": "clear",
            "breakdown": {
                "total_sources": {
                    "result": "clear",
                    "properties": {"total_number_of_sources": "3"},
                }
            },
        },
        "address": {
            "result": "clear",
            "breakdown": {
                "credit_agencies": {
                    "result": "clear",
                    "properties": {"number_of_matches": "1"},
                },
                "telephone_database": {"result": "clear", "properties": {}},
                "voting_register": {"result": "clear", "properties": {}},
            },
        },
        "date_of_birth": {
            "result": "clear",
            "breakdown": {
                "credit_agencies": {"result": "clear", "properties": {}},
                "voting_register": {"result": "clear", "properties": {}},
            },
        },
        "mortality": {"result": "clear"},
    },
    "check_id": CHECK_ID,
    "documents": [],
}

TEST_REPORT_DOCUMENT = {
    "created_at": "2019-10-03T14:05:48Z",
    "documents": [{"id": DOCUMENT_ID}],
    "href": f"/v3/reports/{DOCUMENT_REPORT_ID}",
    "id": DOCUMENT_REPORT_ID,
    "name": "document",
    "properties": {
        "nationality": "",
        "last_name": "Names",
        "issuing_country": "GBR",
        "gender": "",
        "first_name": "Report",
        "document_type": "passport",
        "document_numbers": [{"value": "123456789", "type": "document_number"}],
        "date_of_expiry": "2030-01-01",
        "date_of_birth": "1990-01-01",
    },
    "result": "clear",
    "status": "complete",
    "sub_result": "clear",
    "breakdown": {
        "data_comparison": {
            "result": "clear",
            "breakdown": {
                "issuing_country": {"result": "clear", "properties": {}},
                "gender": {"result": "clear", "properties": {}},
                "date_of_expiry": {"result": "clear", "properties": {}},
                "last_name": {"result": "clear", "properties": {}},
                "document_type": {"result": "clear", "properties": {}},
                "document_numbers": {"result": "clear", "properties": {}},
                "first_name": {"result": "clear", "properties": {}},
                "date_of_birth": {"result": "clear", "properties": {}},
            },
        },
        "data_validation": {
            "result": "clear",
            "breakdown": {
                "gender": {"result": "clear", "properties": {}},
                "date_of_birth": {"result": "clear", "properties": {}},
                "document_numbers": {"result": "clear", "properties": {}},
                "document_expiration": {"result": "clear", "properties": {}},
                "expiry_date": {"result": "clear", "properties": {}},
                "mrz": {"result": "clear", "properties": {}},
            },
        },
        "age_validation": {
            "result": "clear",
            "breakdown": {
                "minimum_accepted_age": {"result": "clear", "properties": {}}
            },
        },
        "image_integrity": {
            "result": "clear",
            "breakdown": {
                "image_quality": {"result": "clear", "properties": {}},
                "conclusive_document_quality": {"result": "clear", "properties": {}},
                "supported_document": {"result": "clear", "properties": {}},
                "colour_picture": {"result": "clear", "properties": {}},
            },
        },
        "visual_authenticity": {
            "result": "clear",
            "breakdown": {
                "fonts": {"result": "clear", "properties": {}},
                "picture_face_integrity": {"result": "clear", "properties": {}},
                "template": {"result": "clear", "properties": {}},
                "security_features": {"result": "clear", "properties": {}},
                "original_document_present": {"result": "clear", "properties": {}},
                "digital_tampering": {"result": "clear", "properties": {}},
                "other": {"result": "clear", "properties": {}},
                "face_detection": {"result": "clear", "properties": {}},
            },
        },
        "data_consistency": {
            "result": "clear",
            "breakdown": {
                "date_of_expiry": {"result": "clear", "properties": {}},
                "document_numbers": {"result": "clear", "properties": {}},
                "issuing_country": {"result": "clear", "properties": {}},
                "document_type": {"result": "clear", "properties": {}},
                "date_of_birth": {"result": "clear", "properties": {}},
                "gender": {"result": "clear", "properties": {}},
                "first_name": {"result": "clear", "properties": {}},
                "last_name": {"result": "clear", "properties": {}},
                "nationality": {"result": "clear", "properties": {}},
            },
        },
        "police_record": {"result": "clear"},
        "compromised_document": {"result": "clear"},
    },
    "check_id": CHECK_ID,
}

TEST_EVENT = {
    "payload": {
        "resource_type": "check",
        "action": "check.form_opened",
        "object": {
            "id": CHECK_ID,
            "status": "complete",
            "completed_at_iso8601": "2019-10-28T15:00:39Z",
            "href": f"https://api.onfido.com/v3/checks/{CHECK_ID}",
        },
    }
}
