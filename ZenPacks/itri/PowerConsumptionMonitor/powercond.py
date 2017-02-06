###################################
# Author: Jaime Andres Alvarez
###################################

import logging
log = logging.getLogger('zen.powercond')
logging.basicConfig()

import Globals
import zope.component
import zope.interface

from twisted.internet import defer

from Products.ZenCollector.daemon import CollectorDaemon
from Products.ZenCollector.interfaces \
    import ICollectorPreferences, IScheduledTask, IEventService, IDataService

from Products.ZenCollector.tasks \
    import SimpleTaskFactory, SimpleTaskSplitter, TaskStates

from Products.ZenUtils.observable import ObservableMixin

from Products.ZenUtils.Utils import unused

from ZenPacks.itri.PowerConsumptionMonitor.services.PowerMonConfigService \
    import PowerMonConfigService

unused(Globals)
unused(PowerMonConfigService)

from Products.ZenEvents.ZenEventClasses import Error, Clear, Critical

class ZenPowerConsumptionMonitorPreferences(object):
    zope.interface.implements(ICollectorPreferences)

    def __init__(self):
        self.collectorName = 'powercond'
        self.configurationService = \
            "ZenPacks.itri.PowerConsumptionMonitor.services.PowerMonConfigService"

        # How often the daemon will collect each device. Specified in seconds.
        self.cycleInterval = 1 * 60

        # How often the daemon will reload configuration. In seconds.
        self.configCycleInterval = 5 * 60

        self.options = None
        
        # Initialize global power consumption acumulator variable
        self.totalPower = 0

        # This list will contain the task IDs in order to determine cycles
        # and when to write to the RRD file.        
        self.task_ids = []
                
    def buildOptions(self, parser):
        pass

    def postStartup(self):
        pass

class ZenPowerConsumptionMonitorTask(ObservableMixin):
    zope.interface.implements(IScheduledTask)

    def __init__(self, taskName, deviceId, interval, taskConfig):
        super(ZenPowerConsumptionMonitorTask, self).__init__()
        self._taskConfig = taskConfig
        
        self._eventService = zope.component.queryUtility(IEventService)
        self._dataService = zope.component.queryUtility(IDataService)
        self._preferences = zope.component.queryUtility(
            ICollectorPreferences, 'powercond')

        # All of these properties are required to implement the IScheduledTask
        # interface.
        self.name = taskName
        self.configId = deviceId
        self.interval = interval
        self.state = TaskStates.STATE_IDLE

        self._devId = deviceId
        self._manageIp = self._taskConfig.manageIp

        # Data points List obtained from config program
        self._datapoints = self._taskConfig.datapoints		
        
    def doTask(self):
        if (self.name in self._preferences.task_ids):
           # Task is repeated, this means that all tasks have already ran in the previous cycle.
           # Write Total Power for previous cycle to RRD file
           createCmd = self._datapoints[0].get('rrdCmd')
           self._writeRRD(createCmd)
           
           # Reset total power consumption and task list for current run
           self._preferences.totalPower = 0
           self._preferences.task_ids = []
        
        # Push this task to the task list
        self._preferences.task_ids.append(self.name)

        # Value comes from a dictionary inside a list, 1st element.            
        device_power = self._datapoints[0].get('dpValue') 
        log.info("Obtaining Power Consumption from device  %s [%s] | Value: %s Watts", self._devId, self._manageIp, device_power)

        # Increase total power
        self._preferences.totalPower += device_power


    def _writeRRD(self, rrdCmd):
       # Stores the value into an RRD file
       # rrd.put() params:
       # @name : RRD Name (String)
       # @value : Data value to be stored (Number)
       # @rrd_type : RRD Data type, Example: GAUGE, COUNTER, DERIVE, ... (String)
       try:
          from Products.ZenModel.PerformanceConf import performancePath
          from Products.ZenRRD.RRDUtil import RRDUtil

          log.info('Writing into RRD File in %s... | Value: %r (%r)' % ( performancePath('totalPower.rrd'), self._preferences.totalPower, type(self._preferences.totalPower)))
          
          # 1st param: RRD Create Command
          # 2nd param: Step
          rrd = RRDUtil(rrdCmd, 300)          
          value2 = rrd.save("totalPower", self._preferences.totalPower, "GAUGE", min=0, max=None)		# This command will write to zenoss/perf/

          log.info("Finished Writing. Return Value: %s" % (value2))
       except Exception, ex:
          summary = "Unable to save data value into RRD file %s . (Exception: \'%s\')" % \
             ("totalPower.rrd", ex)
          log.error(summary)
          
          # Send Error Event to Zenoss
          self._eventService.sendEvent(dict(
             summary = summary,
             message = 'Error Test',
             component = self._preferences.collectorName,
             eventClass = '/Perf/Snmp',
             device = None,
             severity = Error,
             agent = self._preferences.collectorName
             ))

    def cleanup(self):
        pass

# Utils class for useful static methods
class Utils:

   # Static method that builds a Graph URL using the total power RRD file as a source.
   # The graph URL will be printed in the console when the daemon is started.
   def buildGraphUrl():

      import zlib
      from urllib import urlencode
      from base64 import urlsafe_b64encode
   
      # Returns a URL for the given graph options and date range.
      from Products.ZenModel.PerformanceConf import performancePath

      graph_def = "-F|-E|--width=800|--height=260|--vertical-label=Watts|--title=Power Consumption|"    # Graph Definitions
      url = "/zport/RenderServer"                                                                      # Render Server URL

      # Build the complete URL, using the RRD file.
      # Graph definition contains the Graph height, width, labels, title, RDD source, Line size, line color, among other things...
      graph_def += "DEF:t1=" + performancePath('totalPower.rrd') + ":ds0:AVERAGE|LINE2:t1#00b200:Power Consumption"

      gopts = graph_def.split('|')      # Graph options, obtained from the graph definition
      drange = 129600                   # Data range

      new_opts = []                     # New graph options for the final URL
      width = 0

      # Assign the width to the new URL
      for o in gopts:
         if o.startswith('--width'):
            width = o.split('=')[1].strip()
            continue
         new_opts.append(o)

      encodedOpts = urlsafe_b64encode(zlib.compress('|'.join(new_opts), 9))
      params = {
         'gopts': encodedOpts,
         'drange': drange,
         'width': width,
      }

      if url.startswith('proxy'):
         url = url.replace('proxy', 'http', 1)
         params['remoteUrl'] = url
         return '/zport/RenderServer/render?%s' % (urlencode(params),)
      else:
         return '%s/render?%s' % (url, urlencode(params),)

   buildGraphUrl = staticmethod(buildGraphUrl)


if __name__ == '__main__':
    myPreferences = ZenPowerConsumptionMonitorPreferences()
    myTaskFactory = SimpleTaskFactory(ZenPowerConsumptionMonitorTask)
    myTaskSplitter = SimpleTaskSplitter(myTaskFactory)

    print "Graph URL: "
    print Utils.buildGraphUrl()

    daemon = CollectorDaemon(myPreferences, myTaskSplitter)
    daemon.run()
    
