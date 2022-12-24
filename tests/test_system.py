from roboflo import Task, Transition, Worker, System, Protocol
import pytest


@pytest.mark.usefixtures("make_workers", "make_transitions")
def test_MakingASystem(make_workers, make_transitions):
    hotplate, spincoater, storage, characterization, arm = make_workers

    with pytest.raises(ValueError):
        # duplicate workers are not allowed!
        system = System(
            workers=[hotplate, hotplate, spincoater],
            transitions=[],
        )

    with pytest.raises(ValueError):
        # cant have transitions that involve workers not in the system
        system = System(workers=[hotplate, spincoater], transitions=make_transitions)

    with pytest.raises(ValueError):
        # cant have a starting/ending worker that is not part of the system.

        system = System(
            workers=[hotplate, spincoater], transitions=[], starting_worker=storage
        )
        system = System(
            workers=[hotplate, spincoater], transitions=[], ending_worker=arm
        )


@pytest.mark.usefixtures("make_workers", "make_transitions", "make_tasks")
def test_generatingProtocols(make_workers, make_transitions, make_tasks):
    hotplate, spincoater, storage, characterization, arm = make_workers
    transitions = make_transitions
    spincoat, anneal, rest, characterize = make_tasks

    system = System(
        workers=[hotplate, spincoater, storage, characterization, arm],
        transitions=transitions,
        starting_worker=storage,
        ending_worker=storage,
    )

    protocol1 = system.generate_protocol(
        worklist=[spincoat, anneal, rest, characterize],
        name="protocol_name",
    )
    with pytest.raises(ValueError):
        # cant generate a protocol with a task that is not in the system
        protocol2 = system.generate_protocol(
            worklist=[
                spincoat,
                anneal,
                rest,
                characterize,
                Task(name="test", workers=[storage], duration=1),
            ],
            name="protocol_name",
        )

    protocol2 = system.generate_protocol(
        worklist=[spincoat, anneal, rest, characterize],
        name="protocol2_name",
    )

    assert protocol1 != protocol2

    assert (
        len(protocol1.worklist) == 4 + 5
    )  # 4 tasks, 5 transitions. storage -> spincoater -> hotplate -> storage -> characterization -> storage
    transition_tasks = [
        task for task in protocol1.worklist if isinstance(task, Transition)
    ]
    assert transition_tasks[0].source == system.starting_worker
    assert transition_tasks[-1].destination == system.ending_worker

    protocol3 = system.generate_protocol(
        worklist=[spincoat, anneal, rest, characterize],
        name="protocol3_name",
        starting_worker=spincoater,
        ending_worker=characterization,
    )

    assert (
        len(protocol3.worklist) == 4 + 3
    )  # 4 tasks, 3 transitions. spincoater -> hotplate -> storage -> characterization
    transition_tasks = [
        task for task in protocol3.worklist if isinstance(task, Transition)
    ]
    assert transition_tasks[0].source == spincoater
    assert transition_tasks[-1].destination == characterization
