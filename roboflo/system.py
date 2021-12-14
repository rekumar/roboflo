from roboflo.tasks import Task, Transition, Worker, Protocol
from roboflo.scheduler import Scheduler
from copy import deepcopy
from math import ceil


class System:
    def __init__(
        self,
        workers,
        transitions,
        starting_worker: Worker,
        ending_worker: Worker = None,
    ):
        self.workers = workers
        if starting_worker not in self.workers:
            raise ValueError("The starting Worker must be present in the workers list!")
        self.starting_worker = starting_worker
        self.ending_worker = ending_worker
        self.transitions = {w: {} for w in self.workers}
        for t in transitions:
            self.transitions[t.source][t.destination] = t

        self._protocol_index = 0
        self._protocol_names = []
        self.scheduler = Scheduler(system=self, protocols=[])

    def __generate_transition_task(
        self, task: Task, source: Worker, destination: Worker
    ):
        if source not in self.transitions:
            raise ValueError(
                f"{source} is not a valid worker in this system! Error thrown during transition for {task}"
            )
        if destination not in self.transitions[source]:
            raise ValueError(
                f"No transition task defined from {source} to {destination}!"
            )
        transition_task = deepcopy(self.transitions[source][destination])
        transition_task.immediate = task.immediate
        transition_task.precedent = task.precedent
        return transition_task

    def generate_protocol(
        self, worklist: list, name: str = None, min_start: int = 0
    ) -> list:
        if name is None:
            name = f"sample{self._protocol_index}"
        if name in self._protocol_names:
            raise ValueError(
                f'Protocol by the name "{name}" already exists - please select a unique name!'
            )
        wl = deepcopy(worklist)
        for task0, task1 in zip(wl, wl[1:]):
            task1.precedent = task0  # task1 is preceded by task0

        protocol_worklist = []
        source = self.starting_worker
        for task in wl:
            destination = task.workers[0]
            if source != destination:
                transition_task = self.__generate_transition_task(
                    task, source, destination
                )
                protocol_worklist.append(transition_task)
                task.precedent = transition_task
            protocol_worklist.append(task)
            source = destination  # update location for next task
        if self.ending_worker is not None:
            if destination != self.ending_worker:
                transition_task = self.__generate_transition_task(
                    task, destination, self.ending_worker
                )
                transition_task.precedent = protocol_worklist[-1]
                protocol_worklist.append(transition_task)  # sample ends at storage

        min_start = ceil(min_start)  # must be integer
        for task in protocol_worklist:
            task.min_start = min_start
            min_start += task.duration
        p = Protocol(name=name, worklist=protocol_worklist)

        self._protocol_names.append(name)
        self._protocol_index += 1
        self.scheduler.add_protocols([p])
        return p
