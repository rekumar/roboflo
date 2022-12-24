[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/rekumar/roboflo/HEAD?labpath=.%2FExamples%2Fbasic%20usage.ipynb)
[![PyPI version](https://badge.fury.io/py/roboflo.svg)](https://badge.fury.io/py/roboflo)
[![codecov](https://codecov.io/gh/rekumar/roboflo/branch/master/graph/badge.svg?token=V3LPNLOJOG)](https://codecov.io/gh/rekumar/roboflo)

![roboflo](/docs/roboflo.png)

`pip install roboflo`

Task scheduler for any system with coordinated workers. The original use case is for the Perovskite Automated Spin-Coating Assembly Line (PASCAL) in the Fenning Lab at UC San Diego, where a robotic arm moves small glass slides between stations to perform experiments. 

`roboflo` assumes that you have a set of `Worker`'s that act (independently or in unison) to perform `Task`'s of set duration. Furthermore, one or more `Worker`'s can function to transition between `Task`'s (eg my robot moves a sample from the hotplate to a camera, or my mom moves me from school to soccer practice). These transition moves constitute a special case of `Task`'s , called `Transition`'s. The total set of `Worker`'s and `Transition`'s define your `System`. Sets of `Task`'s are consolidated into `Protocol`'s (eg the same process for five samples or five kids), which are then scheduled (using the `Scheduler` on your `System`) to minimize the total working time. An example schedule is shown below. 

Happy robot-ing!

![Example Schedule](/docs/exampleschedule.jpg)

PS - shoutout to [Taskpacker](https://github.com/Edinburgh-Genome-Foundry/Taskpacker), from which I drew heavy inspiration. `roboflo` carries much of the design philosophy from `Taskpacker`, but uses only Python packages (the backend is Google ORTools as opposed to Numberjack, which can be difficult to install especially on Windows). `roboflo` also introduces `Transitions`, which define a finite state machine, as a critical component in the workflow under the assumption that many robotic platforms involve workers whose specific jobs are to move things between other workers.

