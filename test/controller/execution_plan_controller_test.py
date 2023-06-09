import io
import json
from datetime import datetime, timedelta
from unittest import mock

from src.persistance.execution_plan import ExecutionPlanStatus
from src.service import execution_plan_service
from test import log_default_user


def test_add_new_execution_plan_fails_on_empty_plan_name(a_client):
    log_default_user(a_client)
    data = {
        "plan_name": "",
    }

    response = a_client.post(
        "/view/execution_plan", data=data, content_type="multipart/form-data"
    )

    assert b"Error: Ingrese un nombre de plan" in response.data
    assert execution_plan_service.get_execution_plan(2) is None


def test_add_new_execution_plan_fails_on_empty_geometry_option(a_client):
    log_default_user(a_client)
    data = {"plan_name": "some_plan", "geometry_option": None}

    response = a_client.post(
        "/view/execution_plan", data=data, content_type="multipart/form-data"
    )

    assert b"Error: Ingrese un nombre de plan" not in response.data
    assert b"Error: Seleccione una geometr" in response.data
    assert execution_plan_service.get_execution_plan(2) is None


def test_add_new_execution_plan_fails_on_empty_flow_file(a_client):
    log_default_user(a_client)
    data = {"plan_name": "some_plan", "geometry_option": 1}

    response = a_client.post(
        "/view/execution_plan", data=data, content_type="multipart/form-data"
    )

    assert b"Error: Ingrese un nombre de plan" not in response.data
    assert b"Error: Seleccione una geometr" not in response.data
    assert b"Error: Seleccione un archivo" in response.data
    assert execution_plan_service.get_execution_plan(2) is None


def test_add_new_execution_plan_fails_on_invalid_geometry_option(
    a_client, a_flow_file, a_plan_file, a_project_file
):
    log_default_user(a_client)
    project_file = (io.BytesIO(a_project_file), "project.prj")
    plan_file = (io.BytesIO(a_plan_file), "plan.p01")
    flow_file = (io.BytesIO(a_flow_file), "flow.u01")
    data = {
        "plan_name": "some_plan",
        "geometry_option": 5,
        "project_file": project_file,
        "plan_file": plan_file,
        "flow_file": flow_file,
    }

    response = a_client.post(
        "/view/execution_plan", data=data, content_type="multipart/form-data"
    )

    assert b"Error: Ingrese un nombre de plan" not in response.data
    assert b"Error: Seleccione una geometr" not in response.data
    assert b"Error: Seleccione un archivo" not in response.data
    assert b"Error guardando informaci\xc3\xb3n en la base de datos." in response.data
    assert execution_plan_service.get_execution_plan(2) is None


def test_add_new_execution_plan_success(a_client, a_execution_plan):
    response = a_execution_plan

    assert b"creada con \xc3\xa9xito." in response.data
    execution_plan = execution_plan_service.get_execution_plan(2)
    assert execution_plan is not None
    assert execution_plan.plan_name == "some_plan"
    assert execution_plan.geometry_id == 1
    assert execution_plan.user_id == 1
    assert execution_plan.status == ExecutionPlanStatus.PENDING


@mock.patch("src.service.execution_plan_service.get_execution_plans")
def test_list_geometries_when_there_are_none(get_execution_plans, a_client):
    get_execution_plans.return_value = []
    log_default_user(a_client)

    response = a_client.get("/execution_plan")

    expected_response = {
        "rows": [],
        "total": 0,
    }

    assert json.loads(response.data) == expected_response


def test_list_geometries_when_there_one(a_client):
    log_default_user(a_client)

    response = a_client.get("/execution_plan")

    expected_response = {
        "rows": [
            {
                "created_at": "21/12/2021",
                "plan_name": "ejemplo-ina",
                "id": 1,
                "status": "PENDING",
                "user": "Admin Ina",
            }
        ],
        "total": 1,
    }

    assert json.loads(response.data) == expected_response


def test_list_execution_plan_when_there_two(a_client, a_execution_plan):
    log_default_user(a_client)

    response = a_client.get("/execution_plan")

    expected_response = {
        "rows": [
            {
                "created_at": datetime.now().strftime("%d/%m/%Y"),
                "plan_name": "some_plan",
                "id": 2,
                "status": "PENDING",
                "user": "Admin Ina",
            },
            {
                "created_at": "21/12/2021",
                "plan_name": "ejemplo-ina",
                "id": 1,
                "status": "PENDING",
                "user": "Admin Ina",
            },
        ],
        "total": 2,
    }

    assert json.loads(response.data) == expected_response
