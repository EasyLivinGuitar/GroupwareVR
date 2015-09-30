'''
Learn how to configure a Polhemus device that communicates with an instance
of a Liberty tracker.
'''

import avango
import avango.daemon
import avango.daemon.polhemus
#import polhemus

# enable logging for detailed information on device setup
avango.enable_logging()

# create a station for each target you want to track
s1 = avango.daemon.Station('M1')
s2 = avango.daemon.Station('M2')

# create instance of Polhemus
polhemus = avango.daemon.polhemus.Polhemus()

# add stations (level should correspond to the number of the Marker)
polhemus.stations[1] = s1
polhemus.stations[2] = s2

# start daemon (will enter the main loop)
avango.daemon.run([polhemus])

