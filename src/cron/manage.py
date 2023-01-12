import os
from os.path import join, isfile
from multiprocessing import Pool

from cron import ROOT_PATH
from cron.utils.logger import logger
from shared.utils.factory import factory


def generate_tasks():
    result = list()
    directory = join(ROOT_PATH, 'tasks')
    for item in os.listdir(directory):
        if item in ['__init__.py']:
            continue
        i = join(directory, item)
        if isfile(i):
            module_name = 'cron.tasks.' + item.split('.')[0]
            task = factory(module_name)
            if task is not None:
                result.append(task)
    return result


def run(task):
    try:
        task.start()
    except KeyboardInterrupt:
        return
    except:
        logger.error()


def start():
    tasks = generate_tasks()
    with Pool(processes=len(tasks)) as executor:
        executor.map(run, tasks)
