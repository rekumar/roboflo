from roboflo import Task, Transition, Worker, System
import pytest
from copy import deepcopy
import numpy as np


@pytest.mark.usefixtures("make_workers")
def test_BaseTaskMechanisms(make_workers):
    hotplate, spincoater, storage, characterization, arm = make_workers

    task = Task(
        name="test_task",
        duration=10,
        workers=[hotplate],
    )

    # task contents are assigned properly
    assert task.name == "test_task"
    assert task.duration == 10
    assert task.workers[0] == hotplate
    assert task.precedent is None
    assert task.immediate is False
    assert task.breakpoint is False
    assert task.id.startswith("test_task-")

    # task outputs to dictionary correctly
    print(task.to_dict())
    expected_task_dict = {
        "name": "test_task",
        "details": {},
        "id": task.id,
        "precedent": None,
    }
    task_dict = task.to_dict()
    assert all(task_dict[key] == value for key, value in expected_task_dict.items())

    copied_task = deepcopy(task)
    assert copied_task != task
    assert copied_task.id != task.id

    task2 = Task(
        name="test_task2",
        duration=10,
        workers=[spincoater],
        precedent=task,
        immediate=True,
        breakpoint=True,
    )
    assert task2.precedent == task
    assert task2.immediate is True
    assert task2.breakpoint is True
    task2_dict = task2.to_dict()
    assert task2_dict["precedent"] == task.id


@pytest.mark.usefixtures("make_workers")
def test_CustomTaskDetails(make_workers):
    hotplate, spincoater, storage, characterization, arm = make_workers

    class CustomTask(Task):
        def __init__(self, custom_field, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.custom_field = custom_field

        def generate_details(self):
            return {"custom_field": self.custom_field}

    custom_task = CustomTask(
        name="custom_task",
        duration=10,
        workers=[spincoater],
        custom_field="custom_value",
    )
    custom_task_dict = custom_task.to_dict()
    assert custom_task_dict["details"] == {"custom_field": "custom_value"}


@pytest.mark.usefixtures("make_workers")
def test_TransitionTask(make_workers):
    hotplate, spincoater, storage, characterization, arm = make_workers

    transition = Transition(
        duration=10,
        workers=[arm],
        source=spincoater,
        destination=hotplate,
    )
    assert transition.source == spincoater
    assert transition.destination == hotplate
    assert transition.name == f"{spincoater.name}_to_{hotplate.name}"
    transition_dict = transition.to_dict()
    assert transition_dict["details"]["source"] == spincoater.name
    assert transition_dict["details"]["destination"] == hotplate.name
