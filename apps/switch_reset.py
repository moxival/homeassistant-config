import appdaemon.appapi as appapi
import shelve
import time


#
# App to reset input_boolean, input_select, input_slider, device_tracker to previous values after HA restart
#
#
# Args:
#
# delay - amount of time after restart to set the switches
#
# https://github.com/home-assistant/appdaemon/blob/master/conf/examples/switch_reset.py
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class SwitchReset(appapi.AppDaemon):
    def initialize(self):

        self.device_db = shelve.open(self.args["file"])
        self.listen_event(self.ha_event, "ha_started")
        self.listen_event(self.appd_event, "appd_started")
        self.listen_state(self.state_change, "input_boolean")
        self.listen_state(self.state_change, "input_select")
        self.listen_state(self.state_change, "input_slider")
        self.listen_state(self.state_change, "device_tracker")

    def ha_event(self, event_name, data, kwargs):
        self.log_notify("Home Assistant restart detected. Running switch value reset in {} seconds".format(self.args["delay"]))
        self.run_in(self.set_switches, self.args["delay"])

    def appd_event(self, event_name, data, kwargs):
        self.log_notify("AppDaemon restart detected. Running switch value reset in {} seconds".format(self.args["delay"]))
        self.run_in(self.set_switches, self.args["delay"])

    def state_change(self, entity, attribute, old, new, kwargs):
        # self.log_notify("State change: {} to {}".format(entity, new))
        self.device_db[entity] = new

    def set_switches(self, kwargs):
        self.log_notify("Setting switches")
        # Find out what devices are available.
        # If we don't know about it initialize, if we do set the switch appropriately
        state = self.get_state()
        for entity in state:
            type, id = entity.split(".")
            if type == "input_boolean" or type == "input_select" or type == "input_slider" or type == "device_tracker":
                if entity in self.device_db:
                    if self.device_db[entity] != state[entity]["state"]:
                        self.log_notify(
                            "Setting {} to {} (was {})".format(entity, self.device_db[entity], state[entity]["state"]))
                        new_state = self.set_state(entity, state=self.device_db[entity])
                else:
                    self.log_notify(
                        "Adding {}, setting value to current state ({})".format(entity, state[entity]["state"]))
                    self.device_db[entity] = state[entity]["state"]

    def log_notify(self, message, level="INFO"):
        if "log" in self.args:
            self.log(message)
        if "notify" in self.args:
            self.notify(message)