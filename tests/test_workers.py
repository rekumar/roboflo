from roboflo import Task, Transition, Worker, System
import pytest
from copy import deepcopy
import numpy as np


def test_WorkerEquality():
    # workers with the same name
    worker = Worker(name="test_worker", capacity=1)
    worker_recreated = Worker(name="test_worker", capacity=1)
    assert worker == worker_recreated


def test_WorkerCapacity():
    with pytest.raises(ValueError):
        worker = Worker(name="test_worker", capacity=0)
    with pytest.raises(ValueError):
        worker = Worker(name="test_worker", capacity=-1)
