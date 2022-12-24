from typing import List
from roboflo import Task, Transition, Worker, System
import pytest

### Workers
@pytest.fixture
def make_workers():
    hotplate = Worker(name="hotplate", capacity=25)

    spincoater = Worker(name="spincoater", capacity=1)

    storage = Worker(
        name="storage",
        capacity=45,
    )

    characterization = Worker(name="characterization line", capacity=1)

    arm = Worker(name="arm", capacity=1)

    return [hotplate, spincoater, storage, characterization, arm]


### Tasks
# Task Definitions
class Spincoat(Task):
    def __init__(self, spin_speed: int, *args, **kwargs):
        self.spin_speed = spin_speed
        super().__init__(*args, **kwargs)

    def generate_details(self):
        return {"spin_speed": self.spin_speed}


class Anneal(Task):
    def __init__(self, temperature: int, *args, **kwargs):
        self.temperature = temperature
        super().__init__(*args, **kwargs)

    def generate_details(self):
        return {"temperature": self.temperature}


@pytest.fixture
def make_tasks(make_workers):
    (
        hotplate,
        spincoater,
        storage,
        characterization,
        arm,
    ) = make_workers  # unpack the workers

    spincoat = Spincoat(
        name="spincoat",
        workers=[spincoater],
        duration=60,
        spin_speed=1000,
    )

    anneal = Anneal(
        name="anneal",
        workers=[hotplate],
        duration=60 * 15,
        immediate=True,  # we want to start annealing immediately after the preceding Transition moves the sample to the hotplate!
        temperature=100,
    )
    rest = Task(name="rest", workers=[storage], duration=180, immediate=True)

    characterize = Task(
        name="characterize", workers=[characterization], duration=300, immediate=False
    )

    return [spincoat, anneal, rest, characterize]


@pytest.fixture
def make_transitions(make_workers) -> List[Worker]:
    hotplate, spincoater, storage, characterization, arm = make_workers

    transitions = [
        Transition(duration=28, source=storage, destination=spincoater, workers=[arm]),
        Transition(duration=20, source=spincoater, destination=hotplate, workers=[arm]),
        Transition(duration=15, source=hotplate, destination=storage, workers=[arm]),
        Transition(
            duration=15, source=storage, destination=characterization, workers=[arm]
        ),
        Transition(
            duration=15, source=characterization, destination=storage, workers=[arm]
        ),
    ]
    return transitions


### System


@pytest.fixture
def make_system(make_workers, make_transitions) -> System:
    hotplate, spincoater, storage, characterization, arm = make_workers

    system = System(
        workers=make_workers,
        transitions=make_transitions,
        starting_worker=storage,
        ending_worker=storage,
    )
    return system
