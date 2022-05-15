import io

from celery import Celery
from datetime import datetime
import os
from src import logger, config
from src.persistance.execution_plan import ExecutionPlanStatus
from src.service import execution_plan_service
from src.service.file_storage_service import FileType

os.environ.setdefault("CELERY_CONFIG_MODULE", "src.celery_config")

celery_app = Celery()
celery_app.config_from_envvar("CELERY_CONFIG_MODULE")


@celery_app.task
def simulate(execution_id):
    import win32com.client as client
    from src.service import file_storage_service

    begin = datetime.now()

    base_path = f"C:\\gesina\\{execution_id}"

    file_storage_service.download_files_for_execution(base_path, execution_id)

    logger.info("Loading hec ras")
    RC = None
    try:
        RC = client.Dispatch("RAS507.HECRASCONTROLLER")
        hec_prj = f"{base_path}\\{execution_id}.prj"
        logger.info("Opening project")
        RC.Project_Open(hec_prj)
        logger.info("Obtaining projects names")
        blnIncludeBasePlansOnly = True
        plan_names = RC.Plan_Names(None, None, blnIncludeBasePlansOnly)[1]

        for name in plan_names:
            logger.info(f"Running plan {name}")
            RC.Plan_SetCurrent(name)
            RC.Compute_HideComputationWindow()
            RC.Compute_CurrentPlan(None, None, True)

        logger.info("Ending simulations")
        execution_plan_service.update_execution_plan_status(
            execution_id, ExecutionPlanStatus.FINISHED
        )
    except:
        execution_plan_service.update_execution_plan_status(
            execution_id, ExecutionPlanStatus.ERROR
        )
    finally:
        if RC:
            RC.Project_Close()
            RC.QuitRAS()

    file_storage_service.save_result_for_execution(base_path, execution_id)

    total_seconds = (datetime.now() - begin).total_seconds()

    logger.info(f"Total runtime seconds {total_seconds}")
    return (datetime.now() - begin).total_seconds()


# ONLY FOR TEST PURPOSE
def fake_simulate(execution_id):
    from src.service import file_storage_service

    fake_result_file = io.BytesIO(b"fake_result")
    file_storage_service.save_file(
        FileType.RESULT, fake_result_file, str(execution_id), execution_id
    )
    execution_plan_service.update_execution_plan_status(
        execution_id, ExecutionPlanStatus.FINISHED
    )


def queue_or_fake_simulate(execution_id):
    if config.dry_run:
        fake_simulate(execution_id)
    else:
        logger.info(f"Queueing simulation for {execution_id}")
        simulate.apply_async(
            kwargs={"execution_id": execution_id}, link_error=error_handler.s()
        )


@celery_app.task
def error_handler(request, exc, traceback):
    print("Task {0} raised exception: {1!r}\n{2!r}".format(request.id, exc, traceback))
