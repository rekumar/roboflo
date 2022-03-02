from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
import numpy as np
from roboflo.tasks import Transition
import itertools as itt

### Task Scheduler
class Scheduler:
    def __init__(
        self,
        system,
        protocols,
    ):
        self.system = system
        self.tasklist = []
        self.protocols = []
        self._num_tasks_on_last_solve = 0
        self.enforce_protocol_order = False
        self.add_protocols(protocols)

    def add_protocols(self, protocols):
        new_protocols = [p for p in protocols if p not in self.protocols]
        self.protocols += new_protocols

    def clear_protocols(self):
        self._num_tasks_on_last_solve = 0
        self.protocols = []
        self.tasklist = []

    def _build_tasklist(self, breakpoints=[]):
        self.tasklist = []
        for p in self.protocols:
            taskit = iter(p.worklist)
            reached_breakpoint = False
            while not reached_breakpoint:
                task = next(taskit, None)
                if task is None:
                    break
                self.tasklist.append(task)
                if task in breakpoints:
                    reached_breakpoint = True
            still_immediate = True
            for task in taskit:
                if not task.immediate:
                    still_immediate = False
                if still_immediate or not np.isnan(
                    task.start
                ):  # immediate tasks left, or task is already solved
                    self.tasklist.append(task)

            # for task in p.worklist:
            #     if not found_breakpoint:

            #     if found_breakpoint:
            #         if not np.isnan(task.start): # ie we already solved this task
            #             self.tasklist.append(task)
            #     else:
            #         self.tasklist.append(task)

            #     if (not found_breakpoint) or (not np.isnan(task.start)):
            #         self.tasklist.append(task)
            #     if breakpoint is not None:
            #         if task == breakpoint:
            #             found_breakpoint = True
            #             breakpoint_task = task

    def _initialize_model(self):
        self.model = cp_model.CpModel()
        ending_variables = []
        machine_intervals = {w: [] for w in self.system.workers}
        all_min_starts = [t.min_start for t in self.tasklist]
        if len(all_min_starts) > 0:
            latest_min_start = max(all_min_starts)
        else:
            latest_min_start = 0
        horizon = int(sum([t.duration for t in self.tasklist]) + latest_min_start)

        ### Task Constraints
        for task in self.tasklist:
            if not np.isnan(task.end):  # ie we already solved this task
                task.end_var = self.model.NewConstant(task.end)
            else:
                task.end_var = self.model.NewIntVar(
                    task.duration + task.min_start, horizon, "end " + str(task.id)
                )
                ending_variables.append(task.end_var)

        for task in self.tasklist:
            ## connect to preceding tasks
            if task.immediate and (task.precedent is not None):
                task.start_var = task.precedent.end_var
            else:
                if not np.isnan(task.start):
                    task.start_var = self.model.NewConstant(task.start)
                else:
                    task.start_var = self.model.NewIntVar(
                        task.min_start, horizon, "start " + str(task.id)
                    )
                    if task.precedent is not None:
                        self.model.Add(task.start_var >= task.precedent.end_var)

            ## mark workers as occupied during this task
            interval_var = self.model.NewIntervalVar(
                task.start_var,
                task.duration,
                task.end_var,
                "interval " + str(task.id),
            )
            for w in task.workers:
                machine_intervals[w].append(interval_var)

        # ### Worker Constraints

        for w in self.system.workers:
            intervals = machine_intervals[w]
            if w.capacity > 1:
                demands = [1 for _ in machine_intervals[w]]
                self.model.AddCumulative(intervals, demands, w.capacity)
            else:
                self.model.AddNoOverlap(intervals)

        ### Force sequential tasks to preserve order even if not immediate
        spanning_tasks = {w: [] for w in self.system.workers if w.capacity == 1}
        for protocol in self.protocols:
            t0 = None
            t1 = None
            for i, task0 in enumerate(protocol.worklist):
                if task0 not in self.tasklist:
                    continue
                if not isinstance(task0, Transition):
                    continue
                if task0.destination.capacity == 1:
                    for task1 in protocol.worklist[i:]:
                        if task1 not in self.tasklist:
                            continue
                        if not isinstance(task1, Transition):
                            continue
                        if (
                            task0.destination == task1.source
                        ):  # ie task1 is a transition off of the unit-capacity station
                            duration = self.model.NewIntVar(0, horizon, "duration")
                            interval = self.model.NewIntervalVar(
                                task0.start_var,
                                duration,
                                task1.end_var,
                                "sampleinterval",
                            )
                            spanning_tasks[task0.destination].append(interval)
                            break

        for intervals in spanning_tasks.values():
            self.model.AddNoOverlap(intervals)

        ### Force sample order if flagged
        if self.enforce_protocol_order:
            for protocol, preceding_protocol in zip(self.protocols[1:], self.protocols):
                self.model.Add(
                    protocol.worklist[0].start_var
                    > preceding_protocol.worklist[0].start_var
                )

        objective_var = self.model.NewIntVar(0, horizon, "makespan")
        self.model.AddMaxEquality(objective_var, ending_variables)
        self.model.Minimize(objective_var)

    def _solve_once(self, solve_time):
        self._initialize_model()
        if len(self.tasklist) == self._num_tasks_on_last_solve:
            print(
                f"previous solution still valid - add new protocols before solving again"
            )
            return
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = solve_time
        self.solver.parameters.num_search_workers = 0  # use all cores
        self.solver.Solve(self.model)

        taskidlist = [task.id for task in self.tasklist]
        for s in self.protocols:
            for task in s.worklist:
                if task.id in taskidlist:
                    task.start = self.solver.Value(task.start_var)
                    task.end = self.solver.Value(task.end_var)
                    task._solution_count += 1
        self._num_tasks_on_last_solve = len(self.tasklist)

    def solve(self, solve_time=5, breakpoints=[[]]):
        solvetime_each = solve_time / (1 + len(breakpoints))
        for bp in breakpoints:
            if len(bp) > 0:
                self._build_tasklist(breakpoints=bp)
                self._solve_once(solve_time=solvetime_each)
                print(f"intermediate solution status: {self.solver.StatusName()}")

        self._build_tasklist()
        self._solve_once(solve_time=solvetime_each)
        print(f"solution status: {self.solver.StatusName()}")
        # if status in [3, 4]:
        #     return
        # self.plot_solution()

    def get_tasklist(self, only_recent=False):
        if only_recent:
            ordered_tasks = [
                task for task in self.tasklist if task._solution_count <= 1
            ]
        else:
            ordered_tasks = self.tasklist.copy()
        ordered_tasks.sort(key=lambda x: x.start)
        return ordered_tasks

    def get_tasklist_by_worker(self, only_recent=False):
        ordered_tasks = {}
        for w in self.system.workers:
            if only_recent:
                ordered_tasks[w] = [
                    task
                    for task in self.tasklist
                    if task.workers[0] == w and task._solution_count <= 1
                ]
            else:
                ordered_tasks[w] = [
                    task for task in self.tasklist if task.workers[0] == w
                ]
            ordered_tasks[w].sort(key=lambda x: x.start)
        return ordered_tasks

    def plot_solution(self, ax=None):
        fig, ax = plt.subplots(figsize=(14, 5))

        for idx, p in enumerate(self.protocols):
            color = plt.cm.tab20(idx % 20)
            offset = 0.2 + 0.6 * (idx / len(self.protocols))
            for t in p.worklist:
                for w in t.workers:
                    y = [self.system.workers.index(w) + offset] * 2
                    x = [t.start / 60, t.end / 60]
                    plt.plot(
                        x,
                        y,
                        color=color,
                        # alpha=(max(1 - (t._solution_count - 1) / 5, 0.4)),
                    )

        plt.yticks(
            [i + 0.5 for i in range(len(self.system.workers))],
            labels=[w.name for w in self.system.workers],
        )
        plt.xlabel("Time (minutes)")

        xlim0 = plt.xlim()
        plt.hlines(
            [i for i in range(1, len(self.system.workers))],
            *xlim0,
            colors="k",
            alpha=0.1,
            linestyles="dotted",
        )
        plt.xlim(xlim0)
        ax2 = plt.twiny()
        ax2.set_xlim([x / 60 for x in xlim0])
        ax2.set_xlabel("Time (hours)")
        plt.sca(ax)
        # plt.show()
