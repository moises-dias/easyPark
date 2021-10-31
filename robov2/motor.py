class Motor:
    """ IN1     IN2 | Motor right (top view with front facing up)
        IN3     IN4 | Motor left
        ------------------------------------
        255     0   | ahead
        0       255 | back
        0       0   | idle
        255     255 | brake
    """

    def __init__(self, rpi, IN1, IN2, IN3, IN4):
        self.input = [-1, IN1, IN2, IN3, IN4] # do not use self.input[0]
        self.rpi = rpi
        self.vel = 1    # it ranges from 0 to 1

        # preciso setar o modo dos pwm como output???

    def go(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnLeft(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel)

    def turnRight(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def stop(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def brake(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel)

    def goBack(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel)

    def setVel(self, vel):
        if vel > 1 or vel < 0:
            raise "Seting motor velocity outside 0.0 - 1.0 range!"
        self.vel = vel
