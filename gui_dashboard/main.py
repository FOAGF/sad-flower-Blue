import tkinter as tk
import simplepyble
from threading import Thread


def gen_flower_uuid(srv, cha):
    return f'c55e4011-c55e-4011-00{srv:02}-c55e401100{cha:02}'


FLOWER_THRESHOLD_SRV = gen_flower_uuid(1,0)
MIN_CO2_UUID = gen_flower_uuid(1,1)
MAX_CO2_UUID = gen_flower_uuid(1,2)
MIN_TVOC_UUID = gen_flower_uuid(1,3)
MAX_TVOC_UUID = gen_flower_uuid(1,4)
NUM_LEVELS_UUID = gen_flower_uuid(1,5)
MODE_UUID = gen_flower_uuid(1,6)

FLOWER_AIR_QUALITY_SRV = gen_flower_uuid(2,0)
CURRENT_CO2_UUID = gen_flower_uuid(2,1)
CURRENT_TVOC_UUID = gen_flower_uuid(2,2)
CURRENT_LEVEL_UUID = gen_flower_uuid(2,3)


class ParameterRead:
    def __init__(self, root, peripheral, s_uuid, c_uuid):
        self.root = root
        self.peripheral = peripheral
        self.rvalue = tk.StringVar()
        self.uuid = [s_uuid, c_uuid]

    def read(self):
        read_thread = AsyncRead(self.peripheral, self.uuid)
        self.root.after(0,read_thread.start())
        self.monitor(read_thread)

    def monitor(self, thread):
        global root
        if thread.is_alive():
            # check the thread every 100ms
            root.after(100, lambda: self.monitor(thread))
        else:
            val = thread.result
            if val is not None:
                val = int.from_bytes(val, byteorder="little")
                self.rvalue.set(str(val))


class ParameterWrite(ParameterRead):
    def __init__(self, root, peripheral, s_uuid, c_uuid):
        super().__init__(root, peripheral, s_uuid, c_uuid)
        self.wvalue = tk.StringVar()

    def write(self):
        val = int.to_bytes(int(self.wvalue.get()), length=2, byteorder="little")
        print("wrote value:", val, flush=True)
        self.peripheral.write_request(self.uuid[0], self.uuid[1], val)


class ParameterFrame:
    def __init__(self, parent, peripheral, name):
        self.parent = parent
        self.peripheral = peripheral
        self.frame = tk.LabelFrame(parent, text=name)
        self.frame.pack(padx=10, pady=10)
        self.parameters = []
        self.current_row = 0

    def add_write(self, name, s_uuid, c_uuid):
        param = ParameterWrite(self.parent, self.peripheral, s_uuid, c_uuid)
        label = tk.Label(self.frame, text=name)
        label.grid(row=self.current_row, column=0, padx=5, pady=5)

        value_label = tk.Label(self.frame, textvariable=param.rvalue)
        value_label.grid(row=self.current_row, column=1, padx=5, pady=5)

        entry = tk.Entry(self.frame, textvariable=param.wvalue, width=10)
        entry.grid(row=self.current_row, column=2, padx=5, pady=5)

        button = tk.Button(self.frame, text="Write", command=param.write)
        button.grid(row=self.current_row, column=3, padx=5, pady=5)

        self.parameters.append(param)

        self.current_row += 1

    def add_read(self, name, s_uuid, c_uuid):
        param = ParameterRead(self.parent, self.peripheral, s_uuid, c_uuid)

        label = tk.Label(self.frame, text=name)
        label.grid(row=self.current_row, column=0, padx=5, pady=5)

        value_label = tk.Label(self.frame, textvariable=param.rvalue)
        value_label.grid(row=self.current_row, column=1, padx=5, pady=5)

        self.parameters.append(param)
        self.current_row += 1

    def read_params(self):
        for param in self.parameters:
            param.read()


class RemoteGUI(tk.Tk):
    def __init__(self, flower_peripheral):
        super().__init__()

        self.title("Flower Remote Dashboard")
        self.geometry('680x430')

        self.flower_peripheral = flower_peripheral

        # GUI elements
        self.co2_frame = ParameterFrame(self, flower_peripheral, "CO2 Levels")
        self.co2_frame.add_write("Min CO2:", FLOWER_THRESHOLD_SRV, MIN_CO2_UUID)
        self.co2_frame.add_write("Max CO2:", FLOWER_THRESHOLD_SRV, MAX_CO2_UUID)
        self.co2_frame.add_read("Current CO2:", FLOWER_AIR_QUALITY_SRV, CURRENT_CO2_UUID)

        self.tvoc_frame = ParameterFrame(self, flower_peripheral, "TVOC Levels")
        self.tvoc_frame.add_write("Min TVOC:", FLOWER_THRESHOLD_SRV, MIN_TVOC_UUID)
        self.tvoc_frame.add_write("Max TVOC:", FLOWER_THRESHOLD_SRV, MAX_TVOC_UUID)
        self.tvoc_frame.add_read("Current TVOC:", FLOWER_AIR_QUALITY_SRV, CURRENT_TVOC_UUID)

        self.label_frame = ParameterFrame(self, flower_peripheral, "TVOC Levels")
        self.label_frame.add_write("Current Level:", FLOWER_AIR_QUALITY_SRV, CURRENT_LEVEL_UUID)
        self.label_frame.add_write("Number of Levels:", FLOWER_THRESHOLD_SRV, NUM_LEVELS_UUID)

    def parameter_update(self):
        if not self.flower_peripheral.is_connected():
            print("Flower disconnected, closing GUI")
            self.destroy()
        else:
            self.co2_frame.read_params()
            self.tvoc_frame.read_params()
            self.label_frame.read_params()
            self.after(1000, self.parameter_update)


class AsyncRead(Thread):
    def __init__(self, peripheral, uuid):
        super().__init__()

        self.uuid = uuid
        self.peripheral = peripheral
        self.result = None

    def run(self):
        self.result = self.peripheral.read(self.uuid[0], self.uuid[1])


TARGET = "f6:f3:69:60:38:74"
adapter = simplepyble.Adapter.get_adapters()[0]

print(f"Selected adapter: {adapter.identifier()} [{adapter.address()}]")

adapter.set_callback_on_scan_start(lambda: print("Scan started."))
adapter.set_callback_on_scan_stop(lambda: print("Scan complete."))
adapter.set_callback_on_scan_found(lambda peripheral: print(f"Found {peripheral.identifier()} [{peripheral.address()}]"))

flower_peripheral = None
# Scan for 3 seconds
while flower_peripheral is None:
    adapter.scan_for(3000)
    peripherals = adapter.scan_get_results()
    for p in peripherals:
        if p.address() == TARGET:
            flower_peripheral = p

print("Found flower")
flower_peripheral.connect()

# Create the Tkinter root window
root = RemoteGUI(flower_peripheral)

# Set up periodic parameter updates
root.after(1000, root.parameter_update)

# Start the Tkinter event loop
root.mainloop()

flower_peripheral.disconnect()
