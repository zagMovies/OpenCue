#  Copyright Contributors to the OpenCue Project
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


"""Utility functions used throughout the application."""


from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import sys
import importlib
import inspect

import opencue
from cuesubmit import Constants


def getLimits():
    """Returns a list of limit names from cuebot."""
    return [limit.name() for limit in opencue.api.getLimits()]


def getServices():
    """Returns a list of service names from cuebot."""
    return [service.name() for service in opencue.api.getDefaultServices()]


def getShows():
    """Returns a list of show names from cuebot."""
    return [show.name() for show in opencue.api.getShows()]


def getAllocations():
    """Returns a list of Allocations from cuebot."""
    return opencue.api.getAllocations()


def getPresetFacility():
    """Returns the default facility defined via environment variable, if set."""
    if os.getenv('RENDER_TO', None):
        return os.environ['RENDER_TO']
    if os.getenv('FACILITY', None):
        return os.environ['FACILITY']
    return None


def getFacilities(allocations):
    """Returns a list of facility names from the allocations."""
    default_facilities = [Constants.DEFAULT_FACILITY_TEXT]
    facilities = set(alloc.data.facility for alloc in allocations)
    return default_facilities + list(facilities)

def getCustomScriptParameters(script_path):
    """ From a custom python script with an opencue_render() function, returns its parameters name, value and type

    Supports for simple types (str, int, bool and 3 int-tuples for min/max/default)
    TODO: support float and float range
    TODO: potential bug: we are importing a script that can have unavailable dependencies

    This function must have type hints, ex houdini_prman.py :
    opencue_render(hipFile: str,
                   ropPath: str,
                   startFrame: str='#IFRAME#',
                   endFrame: str='#IFRAME#',
                   halfRes: bool=0,
                   logLevel: tuple=(0, 5, 3))

    note: here we declared start/endFrame as a str with a default value. This is to get the frame token.
    Type hints are not strict constraints, just hints.

    :type script_path: str
    :param script_path: path to a custom script with an inspectable opencue_render() function
    :rtype: str, dict
    :return:  script name to be loaded as a module / dict of parameters (name, value, type) from opencue_render()
    """
    parameters = {}
    _script_dir, script_file = os.path.split(os.path.splitext(script_path)[0])
    sys.path.append(_script_dir)
    _script_module = importlib.import_module(script_file)
    if not 'opencue_render' in dir(_script_module):
        raise NameError(f'Module {script_file} from {_script_dir} does not contain an opencue_render() function')
    signature = inspect.signature(_script_module.opencue_render)
    for param in signature.parameters.values():
        default_value = param.default
        if default_value is inspect.Parameter.empty:
            default_value = param.annotation()  # evaluates the param type, ex: str()
        parameters[param.name] = {'name': param.name,
                                  'value': default_value,
                                  'type': param.annotation}
        if param.annotation is tuple and len(default_value) == 3:
            parameters[param.name].update({'min': default_value[0],
                                           'max': default_value[1],
                                           'value': default_value[2]})

    return script_file, parameters
