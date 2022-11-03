from warnings import warn
import numpy as np
from math import ceil
import json
from copy import deepcopy
from roboflo.utils import generate_id
from abc import ABC
from typing import List


class Worker(ABC):
    """
    This class contains the nuts and bolts to schedule tasks
    for each "worker". Workers are considered single units that
    act to complete tasks.
    """

    def __init__(
        self,
        name: str,
        capacity: int,
        one_task_at_a_time: bool = False,
        initial_fill: int = 0,
    ):
        self.name = name
        self.capacity = capacity
        self.one_task_at_a_time = one_task_at_a_time
        self.initial_fill = initial_fill

    def __hash__(self):
        return hash(str(type(self)))

    def __repr__(self):
        return f"<Worker: {self.name}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (self.name == other.name)


class Task(ABC):
    def __init__(
        self,
        name: str,
        workers: List[Worker],
        duration: int,
        precedent: List["Task"] = [],
        immediate: bool = False,
        details: dict = {},
        breakpoint: bool = False,
        capacity: int = 1,
    ):
        self.name = name
        self.workers = workers
        self.duration = ceil(duration)  # CPSat solver only works with integers
        self.precedent = precedent
        if isinstance(self.precedent, Task):
            self.precedent = [self.precedent]
        self.immediate = immediate
        self.details = details
        self.breakpoint = breakpoint
        self.capacity = capacity
        self._utilized_capacity = 0

        self.id = generate_id(prefix=self.name)
        self.start = np.nan
        self.end = np.nan
        self._solution_count = 0

        if self.capacity > 1:
            for w in self.workers:
                if self.capacity > w.capacity:
                    raise ValueError(
                        f"Task {self.name} has capacity {self.capacity}, which is greater than that of required worker {w.name} with capacity {w.capacity}! Task capacity must be less than or equal to that of its workers!"
                    )  # TODO should we compare against capacity of all workers? or just against the primary worker (ie first in list)
            if self.immediate:
                warn(
                    "Task {self.name} has capacity {self.capacity} and immediate set to True. Schedules will typically be infeasible with immediate tasks of capacity > 1, as preceding Transition tasks cannot complete simultaneously!"
                )

    def generate_details(self) -> float:
        """construct a dictionary of additional details to describe this task.
        these are typically process variables (ie temperature for a heating
        step) that do not affect scheduling, but are important to execute
        the task properly downstream.

        Subclasses of Task should implement this method as necessary
        """
        return {}

    def __repr__(self):
        return f"<Task: {self.name}, runs from {self.start} - {self.end}>"

    def __eq__(self, other):
        return other.id == self.id

    def __deepcopy__(self, memo):
        """deepcopy is implemented this way such that the copied
        Task object gets a unique id.
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            # if k == "precedent":
            #     setattr(
            #         result, k, self.precedent
            #     )  # deepcopy would mess up precedent task id's
            # else:
            setattr(result, k, deepcopy(v, memo))

        result.id = generate_id(
            prefix=result.name
        )  # give a unique id to the copied task
        result._utilized_capacity = 0  # new instance has not been filled at all
        return result

    def to_dict(self):
        out = {
            "name": self.name,
            "start": self.start,
            "id": self.id,
            "details": self.generate_details(),
            "precedent": [p.id for p in self.precedent],
        }

        # if self.precedent is None:
        #     out["precedent"] = None
        # else:
        #     out["precedent"] = self.precedent.id

        return out

    def to_json(self):
        return json.dumps(self.to_dict())


class Transition(Task):
    def __init__(
        self,
        duration: int,
        source: Worker,
        destination: Worker,
        workers: List[Worker],
        precedent: List[Task] = [],
        immediate: bool = False,
        details: dict = {},
    ):
        self.source = source
        self.destination = destination

        super().__init__(
            name=f"{source.name}_to_{destination.name}",
            duration=duration,
            workers=workers,
            precedent=precedent,
            immediate=immediate,
            details=details,
        )

    def generate_details(self):
        return {"source": self.source.name, "destination": self.destination.name}

    def __repr__(self):
        return f"<Transition: {self.name}, runs from {self.start} - {self.end}>"


class Protocol:
    def __init__(
        self,
        name: str,
        worklist: List[Task],
    ):
        self.name = name
        self.worklist = []
        for task in worklist:
            if not isinstance(task, Task):
                raise ValueError("Protocol worklist must be a list of Task objects!")
            self.worklist.append(task)  # copy to generate unique task id
        self.id = generate_id(prefix=self.name)

    def to_dict(self):
        out = {
            "name": self.name,
            "id": self.id,
            "worklist": [task.to_dict() for task in self.worklist],
        }

        return out

    def to_json(self):
        return json.dumps(self.to_dict())

    def __repr__(self):
        output = f"<Protocol> {self.name}\n"
        output += f"Worklist:\n"
        for task in self.worklist:
            output += f"\t{task}\n"
        return output

    def __eq__(self, other):
        """Note that two unique protocols with the same tasks will not be
        shown as equivalent, as Tasks are copied as to have unique id's
        once the Protocol object is constructed. This allows you to duplicate
        a Protocol (eg for repeating an procedure for more samples) without
        your task/protocol id's colliding.
        """
        if isinstance(other, self.__class__):
            return self.worklist == other.worklist
        else:
            return False

    def __key(self):
        return self.worklist

    def __hash__(self):
        return hash(self.__key())
