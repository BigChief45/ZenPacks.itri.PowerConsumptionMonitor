import logging
log = logging.getLogger('zen.powercond')

import Globals
from Products.ZenUtils.Utils import unused
from Products.ZenCollector.services.config import CollectorConfigService

unused(Globals)

class PowerMonConfigService(CollectorConfigService):

    def _filterDevice(self, device):
        # First use standard filtering.
        filter = CollectorConfigService._filterDevice(self, device)

        has_flag = False
        if filter:
           # Return only devices that have a valid 
           # value for Power Data Point (Assigned by ServerMonitor ZenPack)
           try:
              if device.getRRDValue('Power') != None:
                 has_flag = True
           except Exception as e:
              print e

        return CollectorConfigService._filterDevice(self, device) and has_flag

    def _createDeviceProxy(self, device):
        proxy = CollectorConfigService._createDeviceProxy(self, device)
        
        proxy.configCycleInterval = 5 * 60 # 5 minutes
        proxy.datapoints = []

        perfServer = device.getPerformanceServer()

        self._getPowerDp(proxy, device, device.id, None, perfServer)

        return proxy

    def _getPowerDp(
            self, proxy, deviceOrComponent, deviceId, componentId, perfServer
            ):
        try:        
           # Get the ServerDevice RRD Template. Specified by the ServerMonitor ZenPack
           template = deviceOrComponent.getRRDTemplateByName('ServerDevice')

           # Get the Power data point for the device. Specified by the ServerMonitor ZenPack
           dp = template.getRRDDataPoint('Power')
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


if __name__ == '__main__':
    from Products.ZenHub.ServiceTester import ServiceTester
    tester = ServiceTester(PowerMonConfigService)
    def printer(config):
        # Fill this out
        print config.datapoints

    tester.printDeviceProxy = printer
    tester.showDeviceInfo()

