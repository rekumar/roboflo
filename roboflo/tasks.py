import numpy as np
from math import ceil
import json
from copy import deepcopy
from roboflo.helpers import generate_id
from abc import ABC


class Task(ABC):
    def __init__(
        self,
        name: str,
        workers: list,
        duration: int,
        precedent=None,
        immediate: bool = False,
        details: dict = {},
    ):
        self.name = name
        self.workers = workers
        self.duration = ceil(duration)  # CPSat solver only works with integers
        self.precedent = precedent
        self.immediate = immediate
        self.details = details

        self.id = generate_id(prefix=self.name)
        self.start = np.nan
        self.end = np.nan
        self._solution_count = 0

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
            setattr(result, k, deepcopy(v, memo))

        result.id = generate_id(
            prefix=result.name
        )  # give a unique id to the copied task
        return result

    def to_dict(self):
        out = {
            "name": self.name,
            "start": self.start,
            "id": self.id,
            "details": self.generate_details(),
        }
        if self.precedent is None:
            out["precedent"] = None
        else:
            out["precedent"] = self.precedent.id

        return out

    def to_json(self):
        return json.dumps(self.to_dict())


class Worker(ABC):
    """
    This class contains the nuts and bolts to schedule tasks
    for each "worker". Workers are considered single units that
    act to complete tasks.
    """

    def __init__(self, name, capacity, initial_fill=0):
        self.name = name
        self.capacity = capacity
        self.initial_fill = initial_fill

    def __hash__(self):
        return hash(str(type(self)))

    def __repr__(self):
        return f"<Worker: {self.name}>"

    def __eq__(self, other):
        return (type(self) == type(other)) and (self.name == other.name)


class Transition(Task):
    def __init__(
        self,
        duration: int,
        source: Worker,
        destination: Worker,
        workers: list,
        precedent=None,
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

    def __repr__(self):
        return f"<Transition: {self.name}, runs from {self.start} - {self.end}>"


class Protocol:
    def __init__(
        self,
        name: str,
        worklist: list,
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
