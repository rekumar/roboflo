from roboflo.tasks import Task, Transition, Worker, Protocol
from roboflo.scheduler import Scheduler
from copy import deepcopy
from math import ceil


class System:
    def __init__(
        self,
        workers,
        transitions,
        starting_worker: Worker = None,
        ending_worker: Worker = None,
        enforce_protocol_order: bool = False,
    ):
        """Facilitate scheduling of tasks that move between workers

        Args:
            workers (list): list of Worker objects
            transitions (list): list of Transition objects that define moves between Worker's
            starting_worker (Worker, optional): Default Worker at which protocols begin. Defaults to None.
            ending_worker (Worker, optional): Default Worker at which protocols end. Defaults to None.
            enforce_protocol_order (bool, optional): If True, protocols will be executed in the order they are defined. If False, protocol order may shuffle to reduce total runtime. Tasks within a given protocol will always maintain their order. Defaults to False.
        Raises:
            ValueError: [description]
        """
        if len(set(workers)) != len(workers):
            raise ValueError("All workers must have a unique name!")
        self.workers = workers
        if starting_worker not in self.workers:
            raise ValueError("The starting Worker must be present in the workers list!")
        self.starting_worker = starting_worker
        self.ending_worker = ending_worker
        self.transitions = {w: {} for w in self.workers}
        for t in transitions:
            self.transitions[t.source][t.destination] = t

        self._protocols = {}
        self.scheduler = Scheduler(
            system=self, protocols=[], enforce_protocol_order=enforce_protocol_order
        )

    def __generate_transition_task(
        self, task: Task, source: Worker, destination: Worker
    ) -> Transition:
        """Generate a transition task between two workers

        Args:
            task (Task): the task to be executed after the transition
            source (Worker): source worker
            destination (Worker): destination worker

        Raises:
            ValueError: Invalid Worker object
            ValueError: No Transition exists between source and destination

        Returns:
            Transition: task to move between workers
        """
        if source not in self.transitions:
            raise ValueError(
                f"{source} is not a valid worker in this system! Error thrown during transition for {task}"
            )
        if destination not in self.transitions[source]:
            raise ValueError(
                f"No transition task defined from {source} to {destination}!"
            )
        transition_task = deepcopy(self.transitions[source][destination])
        if not transition_task.immediate:
            transition_task.immediate = (
                task.immediate
            )  # if transition task is not immediate by default, use immediacy of the following task
        transition_task.precedent = task.precedent
        return transition_task

    def generate_protocol(
        self,
        worklist: list,
        name: str = None,
        min_start: int = 0,
        starting_worker: Worker = None,
        ending_worker: Worker = None,
    ) -> list:
        if name is None:
            idx = len(self._protocols)
            name = f"sample{idx}"
        if name in self._protocols:
            raise ValueError(
                f'Protocol by the name "{name}" already exists - please select a unique name!'
            )
        wl = deepcopy(worklist)
        for task0, task1 in zip(wl, wl[1:]):
            task1.precedent = task0  # task1 is preceded by task0

        protocol_worklist = []
        if starting_worker is None:
            source = self.starting_worker
        else:
            source = starting_worker
        if source is None:
            raise ValueError(
                "No default starting worker defined for this System, so starting_worker must be specified in .generate_protocol!"
            )

        if ending_worker is None:
            ending_worker = self.ending_worker

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
        if ending_worker is not None:
            if destination != ending_worker:
                transition_task = self.__generate_transition_task(
                    task, destination, ending_worker
                )
                transition_task.precedent = protocol_worklist[-1]
                protocol_worklist.append(transition_task)  # sample ends at storage

        min_start = ceil(min_start)  # must be integer
        for task in protocol_worklist:
            task.min_start = min_start
            min_start += task.duration
        p = Protocol(name=name, worklist=protocol_worklist)

        self._protocols[name] = p
        self.scheduler.add_protocols([p])
        return p
