import threading
import logging
import json
from queue import Queue
from typing import Callable, List
from typehints.dict_types import SystemArgs

from simpy import Environment
from esper import World

from components.Skeleton import Skeleton
from components.Position import Position

message_buffer = Queue()


def consumer_manager(consumers: List[Callable], also_log: bool):
    logger = logging.getLogger(__name__ + '.consumer')
    logging.addLevelName(25, 'SEER')
    logger.setLevel('SEER')
    while True:
        message = message_buffer.get()  # Blocking function
        if message == 'simulator finished':
            break
        if also_log:
            logger.log(25, message)
        for c in consumers:
            c(message)
        message_buffer.task_done()

# TODO: Add support for a custom message builder
def init(consumers: List[Callable], scan_interval: float, also_log=False):
    # Init consumer thread
    # TODO: Remove daemon. Handle simulator exit gracefully.
    #  Maybe push a "END" message to the message_buffer.
    thread = threading.Thread(target=consumer_manager, args=[consumers, also_log])
    thread.start()

    # The producer thread

    def process(kwargs: SystemArgs):
        event_store = kwargs.get('EVENT_STORE', None)
        world: World = kwargs.get('WORLD', None)
        env: Environment = kwargs.get('ENV', None)
        if event_store is None:
            raise Exception("Can't find eventStore")
        elif env is None:
            raise Exception("Can't find env")

        # Puts information about the simulation as the first message in the queue
        # window name, width and height
        simulation_skeleton = world.component_for_entity(1, Skeleton)
        size = json.loads(simulation_skeleton.style)
        base = {
            "timestamp": -1,
            "window_name": simulation_skeleton.id,
            "dimensions": size
        }
        message_buffer.put(base)
        # Scan simulation situation every scan_interval seconds and report
        last_round: dict = {}
        while True:

            new_message = {
                "timestamp": env.now
            }
            for ent, (skeleton, position) in world.get_components(Skeleton, Position):
                if ent == 1:  # Entity 1 is the entire model
                    continue
                elif last_round.get(ent, (0, None))[0] != 0 and not position.changed:
                    last_round[ent] = (2, skeleton.id)
                    continue

                data = {
                    'value': skeleton.value,
                    'x': position.x,
                    'y': position.y,
                    'width': position.w,
                    'height': position.h,
                    'style': skeleton.style
                }

                new_message[skeleton.id] = data
                last_round[ent] = (2, skeleton.id)
                position.changed = False
            # Check for deleted entities
            deleted = []
            for k, v in last_round.items():
                if v[0] == 2:
                    last_round[k] = (1, v[1])
                elif v[0] == 1:
                    deleted.append(v[1])
                    last_round[k] = (0, v[1])
            new_message['deleted'] = deleted
            # Add message to queue
            message_buffer.put(new_message)
            yield env.timeout(scan_interval)

    def clean():
        message_buffer.put('simulator finished')
        thread.join()

    return process, clean
