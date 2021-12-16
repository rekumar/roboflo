from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
import numpy as np
from roboflo.tasks import Transition

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
        self._num_protocols_on_last_solve = 0
        self.add_protocols(protocols)

    def add_protocols(self, protocols):
        new_protocols = [p for p in protocols if p not in self.protocols]
        self.protocols += new_protocols
        self.tasklist += [task for p in new_protocols for task in p.worklist]
        self.horizon = int(sum([t.duration for t in self.tasklist]))

    def _initialize_model(self, enforce_protocol_order):
        self.model = cp_model.CpModel()
        ending_variables = []
        # machine_intervals = {w: [] for w in self.system.workers}
        reservoirs = {
            w: {"times": [], "demands": [], "min_level": 0, "max_level": w.capacity}
            for w in self.system.workers
        }
        for w in self.system.workers:
            if w.initial_fill > 0:
                reservoirs[w]["times"].append(self.model.NewConstant(0))
                reservoirs[w]["demands"].append(w.initial_fill)

        # reservoirs = {w: w.capacity for w in self.system.workers}
        ### Task Constraints
        for task in self.tasklist:
            if not np.isnan(task.end):
                task.end_var = self.model.NewConstant(task.end)
            else:
                task.end_var = self.model.NewIntVar(
                    task.duration + task.min_start, self.horizon, "end " + str(task.id)
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
                        task.min_start, self.horizon, "start " + str(task.id)
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
            # for w in task.workers:
            #     machine_intervals[w].append(interval_var)

            if isinstance(task, Transition):
                emptying_reservoir = reservoirs[task.source]
                filling_reservoir = reservoirs[task.destination]

                emptying_reservoir["times"].append(task.end_var)
                emptying_reservoir["demands"].append(-1)

                filling_reservoir["times"].append(task.start_var)
                filling_reservoir["demands"].append(1)

        ### Worker Constraints
        for kws in reservoirs.values():
            self.model.AddReservoirConstraint(**kws)

        ### Force sample order if flagged
        if enforce_protocol_order:
            for protocol, preceding_protocol in zip(self.protocols[1:], self.protocols):
                self.model.Add(
                    protocol.worklist[0].start_var
                    > preceding_protocol.worklist[0].start_var
                )

        objective_var = self.model.NewIntVar(0, self.horizon, "makespan")
        self.model.AddMaxEquality(objective_var, ending_variables)
        self.model.Minimize(objective_var)

    def solve(self, solve_time=5, enforce_protocol_order=False):
        if len(self.protocols) == self._num_protocols_on_last_solve:
            print(
                f"previous solution still valid - add new protocols before solving again"
            )
            return
        self._initialize_model(enforce_protocol_order=enforce_protocol_order)
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = solve_time
        self.solver.parameters.num_search_workers = 0  # use all cores
        status = self.solver.Solve(self.model)

        print(f"solution status: {self.solver.StatusName()}")
        # if status in [3, 4]:
        #     return
        for s in self.protocols:
            for task in s.worklist:
                task.start = self.solver.Value(task.start_var)
                task.end = self.solver.Value(task.end_var)
                task._solution_count += 1
        self._num_protocols_on_last_solve = len(self.protocols)
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
