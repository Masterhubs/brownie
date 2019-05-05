#!/usr/bin/python3


from pathlib import Path
import shutil
import sys

from brownie.network.contract import ContractContainer
from .build import Build
from . import compiler
from brownie._config import CONFIG, load_project_config

__all__ = ['project', '__project']

__project = True
project = sys.modules[__name__]


FOLDERS = ["contracts", "scripts", "tests"]


def check_for_project(path):
    path = Path(path).resolve()
    for folder in [path]+list(path.parents):
        if folder.joinpath("brownie-config.json").exists():
            return folder
    return None


def new(path=".", ignore_subfolder=False):
    if CONFIG['folders']['project']:
        raise SystemError("Project has already been loaded")
    path = Path(path)
    path.mkdir(exist_ok=True)
    path = path.resolve()
    if not ignore_subfolder:
        check = check_for_project(path)
        if check and check != path:
            raise SystemError("Cannot make a new project inside the subfolder of an existing project.")
    for folder in [i for i in FOLDERS]:
        path.joinpath(folder).mkdir(exist_ok=True)
    if not path.joinpath('brownie-config.json').exists():
        shutil.copy(
            str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
            str(path.joinpath('brownie-config.json'))
        )
    CONFIG['folders']['project'] = str(path)
    sys.path.insert(0, str(path))
    Build()._load()
    return str(path)


def load(path=None):
    if CONFIG['folders']['project']:
        raise SystemError("Project has already been loaded")
    if path is None:
        path = check_for_project('.')
    if not path or not Path(path).joinpath("brownie-config.json").exists():
        raise SystemError("Could not find brownie project")
    path = Path(path).resolve()
    CONFIG['folders']['project'] = str(path)
    sys.path.insert(0, str(path))
    load_project_config()
    compiler.set_solc_version()
    Build()._load()
    result = []
    for name, data in Build().contracts():
        if not data['bytecode']:
            continue
        container = ContractContainer(data)
        globals()[name] = container
        __all__.append(name)
        result.append(container)
        # if running via interpreter, add to main namespace if package was imported via from
        if '__project' in sys.modules['__main__'].__dict__:
            sys.modules['__main__'].__dict__[name] = container
    return result


def compile_source(source):
    result = []
    for name, build in compiler.compile_source(source).items():
        if build['type'] == "interface":
            continue
        result.append(ContractContainer(build))
    return result
