import math
import pigpio

class ColorSensor:
    """ S0  S1        OUT frequency
        0   0   |          off
        0   1   |           2%
        1   0   |          20%
        1   1   |         100%
        --------------------------------
        S2  S3         Fotodiodo   
        0   0   |          Red
        0   1   |         Blue
        1   0   |      w/ Filter
        1   1   |        Green
        --------------------------------
        OUT     Gives a value 0 - 255 of the color filter read
    """
    def __init__(self, rpi, s1, s2, s3, s4, out):
        self.s = [-1, s1, s2, s3, s4]   # do not use self.s[0]
        self.out = out
        self.rpi

        for i in self.s:
            self.rpi.set_mode(i, pigpio.OUTPUT)

        self.rpi.set_mode(i, pigpio.INPUT)

    def readRed(self):
        self.rpi.write(self.s[2], 0)
        self.rpi.write(self.s[3], 0)
        return self.read(self.out)

    def readGreen(self):
        self.rpi.write(self.s[2], 1)
        self.rpi.write(self.s[3], 1)
        return self.read(self.out)

    def readBlue(self):
        self.rpi.write(self.s[2], 0)
        self.rpi.write(self.s[3], 1)
        return self.read(self.out)

    def readAll(self):
        return self.readRed, self.readGreen, self.readBlue

    def readWithoutFilter(self):
        self.rpi.write(self.s[2], 1)
        self.rpi.write(self.s[3], 0)
        return self.read(self.out)

    def color(self):
        colors = [self.readAll()] # returns red, green, blue into a list
        colors_backup = colors.copy()
        
        # Arredonda os valores para o numero mais próximo divisivel por 10
        # e acha o greate common divisor pra achar a ratio de vermelho, verde e azul
        for c in colors:
            c = 10 * round(c / 10)
        div = math.gcd(colors[0], colors[1], colors[2])
        for c in colors:
            c = c / div
        
        red, green, blue = tuple(colors)
        if   red > green and red > blue and green == blue:
            return 'red'
        elif green > red and green > blue and red == blue:
            return 'green'
        elif blue > red and blue > green and red == green:
            return 'blue'
        elif red > blue and green > blue and red == green:
            return 'yellow'
        elif blue > red and green > red and blue == green:
            return 'cyan'
        elif red > green and blue > green and red == blue:
            return 'magenta'
        elif red == green and green == blue and red == blue:
            if colors_backup[0] > 125 and colors_backup[1] > 125 and colors_backup > 125:
                return 'white'
            else:
                return 'black'        
