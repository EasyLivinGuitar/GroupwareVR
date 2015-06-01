# -*- Mode:Python -*-

##########################################################################
#                                                                        #
# This file is part of AVANGO.                                           #
#                                                                        #
# Copyright 1997 - 2009 Fraunhofer-Gesellschaft zur Foerderung der       #
# angewandten Forschung (FhG), Munich, Germany.                          #
#                                                                        #
# AVANGO is free software: you can redistribute it and/or modify         #
# it under the terms of the GNU Lesser General Public License as         #
# published by the Free Software Foundation, version 3.                  #
#                                                                        #
# AVANGO is distributed in the hope that it will be useful,              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the           #
# GNU General Public License for more details.                           #
#                                                                        #
# You should have received a copy of the GNU Lesser General Public       #
# License along with AVANGO. If not, see <http://www.gnu.org/licenses/>. #
#                                                                        #
##########################################################################

'''
AvangoDaemon NG
===============

The AvangoDaemon is an independent instance for communication with
a variety of devices that serve as input data for Avango NG applications.
The AvangoDaemon has its own main loop in which for each device a thread
is running. Therefore the devices are decoupled from the Avango NG
main loop. Via shared memory segment the Avango NG application
exchanges data with the device instances.

On Avango NG application side a DeviceSensor is used to read out data
coming from an appropriate input device. Whereas a DeviceActuator
can be used to send specific commands to the device, for example
see WiimoteActuator to set LEDs or Rumble modes on a connected
Nintendo Wiimote.

On AvangoDaemon side implementations for different devices exist.
Examples are:

Polhemus
    For processing Polhemus.

Examples
========

There are some basic examples within your Avango NG installation,
that show the configuration and usage of these input devices.
'''

from ._polhemus import *
from ._polhemus import _PolhemusHelper

import avango.nodefactory
nodes = avango.nodefactory.NodeFactory('av::daemon::')


class Polhemus(_PolhemusHelper):
    """Avango NG device for processing Polhemus Tracker data.
    Required properties: stations, port."""
    def __init__(self):
        super(Polhemus, self).__init__()
        self._stations = {}

    class StationProxy(object):
        """Proxy object to override the functions that are called on access of
        list values via [] operator."""
        def __init__(self, polhemus):
            self._polhemus = polhemus

        def __getitem__(self, key):
            if key in self._polhemus._stations:
                return self._polhemus._stations[key]
            else:
                return ''

        def __setitem__(self, key, st):
            self._polhemus._stations[key] = st
            return self._polhemus.add_station(key, st.name)

    stations = property(StationProxy)
