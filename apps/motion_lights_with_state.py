import appdaemon.appapi as appapi


#
# App to turn lights on when motion detected then off again after a delay
#
# Use with constrints to activate only for the hours of darkness
#
# Args:
#
# sensor: binary sensor to use as trigger
# entity_on : entity to turn on when detecting motion, can be a light, script, scene or anything else that can be turned on
# entity_off : entity to turn off when detecting motion, can be a light, script or anything else that can be turned off. Can also be a scene which will be turned on
# delay: amount of time after turning on to turn off again. If not specified defaults to 60 seconds.
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class MotionLightsWithState(appapi.AppDaemon):
    def initialize(self):

        self.handle = None
        self.keep_state = {}

        # Check some Params

        # Subscribe to sensors
        if "sensor" in self.args:
            self.sensors = self.args["sensor"].split(",")
            for sensor in self.sensors:
                self.listen_state(self.motion, sensor)
        else:
            self.log("No sensor specified, doing nothing")

        if "light" in self.args:
            lights = self.args["light"].split(",")
            for light in lights:
                self.listen_state(self.off, light)
        else:
            self.log("No entity to turn on specified")

    def motion(self, entity, attribute, old, new, kwargs):
        if "delay" in self.args:
            delay = self.args["delay"]

            if type(delay) == str and '.' in delay:
                try:
                    delay = int(float(self.get_state(delay))) * 60
                except ValueError:
                    self.log("Invalid delay given: {}".format(delay))
                    delay = 60
        else:
            delay = 60

        if new == "on":
            if self.handle == None:
                if "light" in self.args:
                    lights = self.args["light"].split(",")
                    for light in lights:
                        self.keep_state[light] = int(float(self.get_state(light, "brightness")))

                        self.log("Motion detected: turning {} on at {} for {} s".format(light, self.args["light_brightness"], delay))
                        self.turn_on(light, brightness = self.args["light_brightness"])

                self.handle = self.run_in(self.return_state, delay)
            else:
                self.cancel_timer(self.handle)
                self.handle = self.run_in(self.return_state, delay)

    def off(self, entity, attribute, old, new, kwargs):
        if self.get_state(entity) == "off":
            self.log("reset handle, because {} was turned off".format(entity))
            self.cancel_timer(self.handle)
            self.handle = None

    def return_state(self, kwargs):
        for light in self.keep_state:
            if self.keep_state[light] == 0:
                self.log("Turning {} off".format(light))
                self.turn_off(light)
            else:
                self.log("Restoring {} at {} brightness".format(light, self.keep_state[light]))
                self.call_service("light/turn_on", entity_id  = light, brightness = self.keep_state[light])

        self.handle = None

