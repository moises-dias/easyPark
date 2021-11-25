# coding=utf-8


class coneBot():
    def __init__(self):
        self.run()

    def run(self):

        while True:
            while True:
                print('SIMULANDO ROLEZINHO DO ROBO POR 3 SEGUNDOS')
                sleep(3)
                break
            print('INDO PRA move_on_parking_lot_from_message')
            next_node = ''
            next_face = ''
            self.move_on_parking_lot_from_message(next_node, next_face)

    def move_on_parking_lot_from_message(self, destination_node: int, destination_face: str):
        print("Getting foto! smile :)")


if __name__ == "__main__":

    c = coneBot()
