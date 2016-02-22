"""
ExampleConfigService
ZenHub service for providing configuration to the zenexample collector daemon.

    This provides the daemon with a dictionary of datapoints for every device.
"""

import logging
log = logging.getLogger('zen.powercond')

import Globals
from Products.ZenUtils.Utils import unused
from Products.ZenCollector.services.config import CollectorConfigService

unused(Globals)

# Your daemon configuration service should almost certainly subclass
# CollectorConfigService to make it as easy as possible for you to implement.
class PowerMonConfigService(CollectorConfigService):
    """
    ZenHub service for the zenexample collector daemon.
    """

    # When the collector daemon requests a list of devices to poll from ZenHub
    # your service can filter the devices that are returned by implementing
    # this _filterDevice method. If _filterDevice returns True for a device,
    # it will be returned to the collector. If _filterDevice returns False, the
    # collector daemon won't collect from it.
    def _filterDevice(self, device):
        # First use standard filtering.
        filter = CollectorConfigService._filterDevice(self, device)

        # If the standard filtering logic said the device shouldn't be filtered
        # we can setup some other contraint.
        
        has_flag = False			# Flag to determine if should filter devise
        if filter:
           # Return only devices that have a valid value for Power Data Point (Assigned by ServerMonitor ZenPack)
           try:
              if device.getRRDValue('Power') != None:
                 has_flag = True
           except Exception as e:
              print e

        return CollectorConfigService._filterDevice(self, device) and has_flag

    # The _createDeviceProxy method allows you to build up the DeviceProxy
    # object that will be sent to the collector daemon. Whatever is returned
    # from this method will be sent as the device's representation to the
    # collector daemon. Use serializable types. DeviceProxy works, as do any
    # simple Python types.
    def _createDeviceProxy(self, device):
        proxy = CollectorConfigService._createDeviceProxy(self, device)
        
        proxy.configCycleInterval = 5 * 60 					# 5 minutes
        proxy.datapoints = []

        perfServer = device.getPerformanceServer()

        self._getPowerDp(proxy, device, device.id, None, perfServer)


        return proxy

    # This is not a method we must implement. It is used by the custom
    # _createDeviceProxy method above.
    def _getPowerDp(
            self, proxy, deviceOrComponent, deviceId, componentId, perfServer
            ):
        
        try:        
           # Get the ServerDevice RRD Template. Specified by the ServerMonitor ZenPack
           template = deviceOrComponent.getRRDTemplateByName('ServerDevice')

        
           # Get the Power data point for the device. Specified by the ServerMonitor ZenPack
           dp = template.getRRDDataPoint('Power')
        
           # Get the value
           dp_value = deviceOrComponent.getRRDValue('Power')

           dpInfo = dict(
              devId = deviceId,
              dpId = dp.getId(),
              rrdCmd = perfServer.getDefaultRRDCreateCommand(),
              dpValue = dp_value
              )
                      
           proxy.datapoints.append(dpInfo)
        
        except Exception as e:
           print e


# For diagnostic purposes, allow the user to show the results of the
# proxy creation.
# Run this service as a script to see which devices will be sent to the daemon.
# Add the --device=name flag to see the detailed contents of the proxy that
# will be sent to the daemon
#
if __name__ == '__main__':
    from Products.ZenHub.ServiceTester import ServiceTester
    tester = ServiceTester(PowerMonConfigService)
    def printer(config):
        # Fill this out
        print config.datapoints
        

    tester.printDeviceProxy = printer
    tester.showDeviceInfo()

