from typing import List
from roboflo import Task, Transition, Worker, System, Protocol
import pytest
import numpy as np
import matplotlib.pyplot as plt


def confirm_protocol_is_in_order(protocol: Protocol) -> bool:
    """Given a protocol, returns True if all steps are in order. Additionally, immediate steps must start exactly when the preceding step ends.

    Args:
        protocol (Protocol): a solved Protocol

    Returns:
        bool: True if the protocol is solved correctly
    """
    for task, following in zip(protocol.worklist, protocol.worklist[1:]):
        if following.immediate:
            if task.end != following.start:
                return False
        else:
            if task.end > following.start:
                return False
    return True


def confirm_worker_capacity_respected(system: System) -> bool:
    """Given a system with solved schedule, returns True if worker capacity is respected.

    Args:
        system (System): a system which has been loaded with protocols and solved.

    Returns:
        bool: True if the protocols are solved to not exceed worker capacity
    """
    for worker, worker_tasklist in system.scheduler.get_tasklist_by_worker(
        only_recent=False, json=False
    ).items():
        if len(worker_tasklist) == 0:
            continue
        current_load = 0
        end_time = max([task.end for task in worker_tasklist])

        current_time = 0
        while current_time < end_time:
            for task in worker_tasklist:
                if task.start == current_time:
                    current_load += 1
                elif task.end == current_time:
                    current_load -= 1
            if current_load > worker.capacity:
                return False
            current_time += 1
    return True


def confirm_breakpoints_respected(protocols: List[Protocol]) -> bool:
    breakpoint_tasks = []
    past_breakpoint_tasks = []
    for protocol in protocols:
        found_breakpoint = False
        still_immediate = True
        for task in protocol.worklist:
            if not found_breakpoint:
                if task.breakpoint:
                    found_breakpoint = True
                    breakpoint_tasks.append(task)
            else:
                if still_immediate and task.immediate:
                    breakpoint_tasks.append(task)
                else:
                    still_immediate = False
                    past_breakpoint_tasks.append(task)

    return max([task.start for task in breakpoint_tasks]) <= min(
        [task.start for task in past_breakpoint_tasks]
    )


@pytest.mark.usefixtures("make_system", "make_tasks")
def test_BasicScheduling(make_system, make_tasks):
    system: System = make_system
    spincoat, anneal, rest, characterize = make_tasks

    ## single protocol
    protocol = system.generate_protocol(
        worklist=[spincoat, anneal, rest, characterize],
    )
    system.scheduler.solve()
    # ensure the protocol is in order
    assert confirm_protocol_is_in_order(
        protocol
    ), "After solving the schedule, a protocol was not in order!"

    ## multiple protocols
    protocol2 = system.generate_protocol(
        worklist=[spincoat, anneal, rest, characterize],
    )
    system.scheduler.solve()

    assert confirm_protocol_is_in_order(
        protocol2
    ), "After solving the schedule, a protocol was not in order!"

    assert confirm_worker_capacity_respected(
        system
    ), "After solving the schedule, a worker was over capacity!"

    # return results properly

    tasklist = system.scheduler.get_tasklist()
    all_tasks = protocol.worklist + protocol2.worklist
    all_tasks_workers = [
        task
        for tasklist in system.scheduler.get_tasklist_by_worker().values()
        for task in tasklist
    ]
    for task in tasklist:
        assert (
            task in all_tasks
        ), "Tasklist returned a task that was not in the protocols!"
        assert (
            task in all_tasks_workers
        ), "Tasklist_by_worker returned a task that was not in the protocols!"

        all_tasks.remove(task)
        all_tasks_workers.remove(task)

    assert len(all_tasks) == 0, "Some protocol tasks were not returned in get_tasklist!"
    assert (
        len(all_tasks_workers) == 0
    ), "Some protocol tasks were not returned in get_tasklist_by_worker!"

    recent_tasklist = system.scheduler.get_tasklist(only_recent=True)
    recent_tasklist_workers = [
        task
        for tasklist in system.scheduler.get_tasklist_by_worker(
            only_recent=True
        ).values()
        for task in tasklist
    ]
    for task in recent_tasklist:
        assert (
            task not in protocol.worklist
        ), "Recent tasklist returned a task that was in the first protocol!"

    for task in recent_tasklist_workers:
        assert (
            task not in protocol.worklist
        ), "Recent tasklist_by_worker returned a task that was in the first protocol!"

    system.scheduler.plot_solution()

    fig, ax = plt.subplots()
    system.scheduler.plot_solution(ax=ax)


@pytest.mark.usefixtures("make_system", "make_tasks")
def test_GroupScheduling(make_system, make_tasks):
    system = make_system
    spincoat, anneal, rest, characterize = make_tasks

    ## single protocol
    protocols = []
    for i in range(10):
        protocols.append(
            system.generate_protocol(
                worklist=[spincoat, anneal, rest, characterize],
            )
        )
    system.scheduler.solve()

    # ensure the protocols are in order
    for protocol in protocols:
        assert confirm_protocol_is_in_order(
            protocol
        ), "After solving the schedule, a protocol was not in order!"

    assert confirm_worker_capacity_respected(
        system
    ), "After solving the schedule, a worker was over capacity!"


@pytest.mark.usefixtures("make_system", "make_tasks")
def test_OnlineScheduling(make_system, make_tasks):
    # e will test adding a new protocol after some of the earlier protocols have ended. Similar to online learning situation where protocols are added after some preceding ones are completed + their data is processed.

    system: System = make_system
    spincoat, anneal, rest, characterize = make_tasks

    ## initial protocols
    protocols = []
    for i in range(5):
        protocols.append(
            system.generate_protocol(
                worklist=[spincoat, anneal, rest, characterize],
            )
        )
    system.scheduler.solve()

    ### Online scheduling _without_ flexing downstream schedule
    intermediate_start_time = protocols[2].worklist[-1].end

    intermediate_protocol = system.generate_protocol(
        worklist=[spincoat, anneal, rest, characterize],
        min_start=intermediate_start_time,
    )
    system.scheduler.solve()

    assert confirm_protocol_is_in_order(
        intermediate_protocol
    ), "After solving the schedule, the intermediate protocol was not in order!"
    assert confirm_worker_capacity_respected(
        system
    ), "After solving the schedule, a worker was over capacity!"

    ### Online scheduling _with_ flexing downstream schedule
    intermediate_start_time = protocols[3].worklist[-1].end

    system.scheduler.flex(intermediate_start_time)
    assert np.isnan(
        protocols[-1].worklist[-1].end
    ), "After flexing, the end time of the last protocol was not nan!"
    intermediate_protocol = system.generate_protocol(
        worklist=[spincoat, anneal, rest, characterize],
        min_start=intermediate_start_time,
    )
    system.scheduler.solve()

    assert confirm_protocol_is_in_order(
        intermediate_protocol
    ), "After solving the schedule, the intermediate protocol was not in order!"
    assert confirm_worker_capacity_respected(
        system
    ), "After solving the schedule, a worker was over capacity!"


@pytest.mark.usefixtures("make_system", "make_workers")
def test_Breakpoints(make_system, make_workers):
    system: System = make_system
    hotplate, spincoater, storage, characterization, arm = make_workers

    task1 = Task(name="task1", duration=10, workers=[spincoater], breakpoint=True)
    task2 = Task(
        name="task2",
        duration=2,
        workers=[hotplate],
        immediate=True,
    )
    task3 = Task(
        name="task3",
        duration=2,
        workers=[storage],
    )

    ## initial protocols
    protocols = []
    for i in range(10):
        protocols.append(
            system.generate_protocol(
                worklist=[task1, task2, task3], starting_worker=spincoater
            )
        )
    system.scheduler.solve()

    # ensure the protocol is in order and workers were not over capacity
    for protocol in protocols:
        assert confirm_protocol_is_in_order(
            protocol
        ), "After solving the schedule, a protocol was not in order!"

    assert confirm_worker_capacity_respected(
        system
    ), "After solving the schedule, a worker was over capacity!"

    assert confirm_breakpoints_respected(protocols), "Breakpoints were not respected!"


@pytest.mark.usefixtures("make_system", "make_workers")
def test_EnforceScheduleOrder_and_ClearProtocols(make_system, make_workers):
    system: System = make_system
    hotplate, spincoater, storage, characterization, arm = make_workers

    short_task1 = Task(name="task1", duration=1, workers=[spincoater])
    long_task1 = Task(name="task1", duration=1000, workers=[spincoater])
    task2 = Task(
        name="task2",
        duration=2,
        workers=[hotplate],
        immediate=True,
    )
    task3 = Task(
        name="task3",
        duration=2,
        workers=[storage],
    )

    ### Order is not enforced
    long_protocol = system.generate_protocol(
        worklist=[long_task1, task2, task3], starting_worker=spincoater
    )
    short_protocols = []
    for i in range(10):
        short_protocols.append(
            system.generate_protocol(
                worklist=[short_task1, task2, task3], starting_worker=spincoater
            )
        )
    system.scheduler.solve()

    assert (
        long_protocol.worklist[0].start > 0
    ), "Long protocol was scheduled first when it was not supposed to!"

    # ### Order is enforced
    system.scheduler.flex(0)  # reset the schedule
    system.scheduler.enforce_protocol_order = True
    system.scheduler.solve()

    assert (
        long_protocol.worklist[0].start == 0
    ), "Long protocol was not scheduled first when it supposed to be!"
