from multiprocessing.sharedctypes import Value
from WF_SDK import *  # import instruments
from WF_SDK.dmm import *
from power_supply import PowerSupply
import time
import subprocess
import sys
from ctypes import *
import logging
import os

# import flash


def accurate_delay(delay):
    """Function to provide accurate time delay in millisecond"""
    _ = time.perf_counter() + delay / 1000
    while time.perf_counter() < _:
        pass


class Test:
    def __init__(
        self,
        device1v8,
        device3v3,
        deviced=None,
        test_name=None,
        passing_criteria=[],
        voltage=1.6,
        sram=1,
    ):
        self.device1v8 = device1v8
        self.device3v3 = device3v3
        self.deviced = deviced
        self.rstb = self.device1v8.dio_map["rstb"]
        self.gpio_mgmt = self.device1v8.dio_map["gpio_mgmt"]
        self.test_name = test_name
        self.voltage = voltage
        self.sram = sram
        self.passing_criteria = passing_criteria

    def receive_packet(self, pulse_width=25):
        """recieves packet using the wire protocol, uses the gpio_mgmt I/O

        Returns:
            int: pulse count
        """
        ones = 0
        pulses = 0
        self.gpio_mgmt.set_state(False)
        while self.gpio_mgmt.get_value() != False:
            pass
        state = "LOW"
        accurate_delay(pulse_width / 2.0)
        for i in range(0, 30):
            accurate_delay(pulse_width)
            x = self.gpio_mgmt.get_value()
            if state == "LOW":
                if x:
                    state = "HI"
            elif state == "HI":
                if not x:
                    state = "LOW"
                    ones = 0
                    pulses = pulses + 1
            if x:
                ones = ones + 1
            if ones > 3:
                break
        # print("A packet has been received!")
        return pulses

    def send_packet(self, num_pulses, pulse_width=25):
        num_pulses = num_pulses + 1
        self.gpio_mgmt.set_state(True)
        self.gpio_mgmt.set_value(1)
        time.sleep(5)
        for i in range(0, num_pulses):
            self.gpio_mgmt.set_value(0)
            accurate_delay(pulse_width)
            self.gpio_mgmt.set_value(1)
            accurate_delay(pulse_width)

    def send_pulse(self, num_pulses, channel, pulse_width=25):
        if channel < 14:
            channel = self.device1v8.dio_map[channel]
        elif channel > 21:
            channel = self.device3v3.dio_map[channel]
        elif self.deviced:
            channel = self.deviced.dio_map[channel]

        channel.set_state(True)
        channel.set_value(1)
        num_pulses = num_pulses + 1
        time.sleep(5)
        for i in range(0, num_pulses):
            channel.set_value(0)
            accurate_delay(pulse_width)
            channel.set_value(1)
            accurate_delay(pulse_width)

    def reset(self, duration=1):
        """applies reset to the caravel board

        Args:
            duration (int, optional): duration of reset. Defaults to 1.
        """
        # logging.info("   applying reset on channel 0 device 1")
        # self.rstb.set_value(0)
        self.apply_reset()
        time.sleep(duration)
        # self.rstb.set_value(1)
        self.release_reset()
        time.sleep(duration)
        # logging.info("   reset done")

    def apply_reset(self):
        """applies reset to the caravel board

        Args:
            duration (int, optional): duration of reset. Defaults to 1.
        """
        logging.info("   applying reset on channel 0 device 1")
        self.rstb.set_state(True)
        self.rstb.set_value(0)

    def release_reset(self):
        """applies reset to the caravel board

        Args:
            duration (int, optional): duration of reset. Defaults to 1.
        """
        logging.info("   releasing reset on channel 0 device 1")
        self.rstb.set_state(False)
        # self.rstb.set_value(1)

    def flash(self, hex_file):
        """flashes the caravel board with hex file,
        uses caravel_board/firmware_vex/util/caravel_hkflash.py script

        Args:
            hex_file (string): path to hex file
        """
        sp = subprocess.run(
            f"python3 caravel_hkflash.py {hex_file}",
            cwd="./caravel_board/firmware_vex/util/",
            shell=True,
        )
        ret_code = sp.returncode
        if ret_code != 0:
            logging.error("Can't flash!")
            self.close_devices()
            os._exit(1)


        # flash.erase()
        # if flash.flash(hex_file):
        #     logging.error("Can't flash!")
        #     self.close_devices()
        #     sys.exit()

    def change_voltage(self):
        """
        changes voltage output of the device connected to `VCORE` power supply
        """
        self.device1v8.supply.set_voltage(self.voltage)

    def exec_flashing(self):
        """
        Automates flashing based on sram of DFFRAM, and test name
        """
        logging.info("   Flashing CPU")
        self.apply_reset()
        self.powerup_sequence()
        if self.sram == 1:
            self.flash(f"silicon_tests/{self.test_name}/{self.test_name}_sram.hex")
        else:
            self.flash(f"silicon_tests/{self.test_name}/{self.test_name}_dff.hex")
        self.release_reset()
        self.powerup_sequence()
        logging.info(f"   changing VCORE voltage to {self.voltage}v")
        self.device1v8.supply.set_voltage(self.voltage)
        self.reset()

    def powerup_sequence(self):
        """
        Power supply powerup sequence:
            turns off both devices
            turns on device and change voltage to the required one
        """
        self.device1v8.supply.turn_off()
        self.device3v3.supply.turn_off()
        time.sleep(5)
        logging.info("   Turning on VIO with 3.3v")
        self.device3v3.supply.set_voltage(3.3)
        time.sleep(1)
        logging.info(f"   Turning on VCORE with {self.voltage}v")
        self.device1v8.supply.set_voltage(self.voltage)
        time.sleep(1)

    def power_down(self):
        """
        Power supply powerup sequence:
            turns off both devices
            turns on device and change voltage to the required one
        """
        self.device1v8.supply.turn_off()
        self.device3v3.supply.turn_off()
        time.sleep(5)
        # logging.info("   Turning on VIO with 3.3v")
        # self.device3v3.supply.set_voltage(3.3)
        # time.sleep(1)
        # logging.info(f"   Turning on VCORE with {self.voltage}v")
        # self.device1v8.supply.set_voltage(self.voltage)
        # time.sleep(1)

    def power_up(self):
        """
        Power supply powerup sequence:
            turns off both devices
            turns on device and change voltage to the required one
        """
        # self.device1v8.supply.turn_off()
        # self.device3v3.supply.turn_off()
        # time.sleep(5)
        logging.info("   Turning on VIO with 3.3v")
        self.device3v3.supply.set_voltage(3.3)
        time.sleep(1)
        logging.info(f"   Turning on VCORE with {self.voltage}v")
        self.device1v8.supply.set_voltage(self.voltage)
        time.sleep(1)

    def power_up_1v8(self):
        """
        Power supply powerup sequence:
            turns off both devices
            turns on device and change voltage to the required one
        """
        # self.device1v8.supply.turn_off()
        # self.device3v3.supply.turn_off()
        # time.sleep(5)
        logging.info("   Turning on VIO with 3.3v")
        self.device3v3.supply.set_voltage(3.3)
        time.sleep(1)
        logging.info(f"   Turning on VCORE with 1.8v")
        self.device1v8.supply.set_voltage(1.8)
        time.sleep(1)

    def turn_off_devices(self):
        """
        turns off all devices
        """
        self.device1v8.supply.turn_off()
        self.device3v3.supply.turn_off()
        # self.deviced.supply.turn_off()

    def close_devices(self):
        """
        turns off devices and closes them
        """
        self.device1v8.supply.turn_off()
        self.device3v3.supply.turn_off()
        # self.deviced.supply.turn_off()
        device.close(self.device1v8)
        device.close(self.device3v3)
        # device.close(self.deviced)

    def reset_devices(self):
        # dwf.FDwfDigitalOutReset(self.device1v8.handle)
        # dwf.FDwfDigitalOutReset(self.device3v3.handle)
        # dwf.FDwfDigitalOutReset(self.deviced.handle)
        # dwf.DwfDeviceReset(self.device1v8.handle)
        # dwf.DwfDeviceReset(self.device3v3.handle)
        # dwf.DwfDeviceReset(self.deviced.handle)

        for c in self.device1v8.dio_map:
            self.device1v8.dio_map[c].set_state(False)
        for c in self.device3v3.dio_map:
            self.device3v3.dio_map[c].set_state(False)
        for c in self.deviced.dio_map:
            self.deviced.dio_map[c].set_state(False)


class Device:
    """
    Device class to initialize devices
    """

    def __init__(self, device, id, dio_map):
        self.ad_device = device
        self.id = id
        self.dio_map = dio_map
        self.handle = device.handle
        self.supply = PowerSupply(self.ad_device)


class Dio:
    def __init__(self, channel, device_data, state=False):
        self.device_data = device_data
        self.channel = channel
        self.state = self.set_state(state)

    def get_value(self):
        """
        get the state of a DIO line
        parameters: - device data
                    - selected DIO channel number
        returns:    - True if the channel is HIGH, or False, if the channel is LOW
        """
        # load internal buffer with current state of the pins
        dwf.FDwfDigitalIOStatus(self.device_data.handle)

        # get the current state of the pins
        data = ctypes.c_uint32()  # variable for this current state
        dwf.FDwfDigitalIOInputStatus(self.device_data.handle, ctypes.byref(data))

        # convert the state to a 16 character binary string
        data = list(bin(data.value)[2:].zfill(16))

        # check the required bit
        if data[15 - self.channel] != "0":
            value = True
        else:
            value = False
        return value

    def set_state(self, state):
        """
        set a DIO line as input, or as output
        parameters: - device data
                    - selected DIO channel number
                    - True means output, False means input
        """
        # load current state of the output enable buffer
        mask = ctypes.c_uint16()
        dwf.FDwfDigitalIOOutputEnableGet(self.device_data.handle, ctypes.byref(mask))

        # convert mask to list
        mask = list(bin(mask.value)[2:].zfill(16))

        # set bit in mask
        if state:
            mask[15 - self.channel] = "1"
        else:
            mask[15 - self.channel] = "0"

        # convert mask to number
        mask = "".join(element for element in mask)
        mask = int(mask, 2)

        # set the pin to output
        dwf.FDwfDigitalIOOutputEnableSet(self.device_data.handle, ctypes.c_int(mask))

    def set_value(self, value):
        """
        set a DIO line as input, or as output
        parameters: - device data
                    - selected DIO channel number
                    - True means HIGH, False means LOW
        """
        if self.state is True:
            logging.error("can't set value for an input pin")
        else:
            # load current state of the output state buffer
            mask = ctypes.c_uint16()
            dwf.FDwfDigitalIOOutputGet(self.device_data.handle, ctypes.byref(mask))

            # convert mask to list
            mask = list(bin(mask.value)[2:].zfill(16))

            # set bit in mask
            if value:
                mask[15 - self.channel] = "1"
            else:
                mask[15 - self.channel] = "0"

            # convert mask to number
            mask = "".join(element for element in mask)
            mask = int(mask, 2)

            # set the pin state
            dwf.FDwfDigitalIOOutputSet(self.device_data.handle, ctypes.c_int(mask))

        return


class UART:
    def __init__(self, device_data):
        self.device_data = device_data
        self.rx = 8
        # self.tx = 5
        self.tx = 7

    def open(self, baud_rate=9600, parity=None, data_bits=8, stop_bits=1):
        """
        initializes UART communication

        parameters: - device data
                    - rx (DIO line used to receive data)
                    - tx (DIO line used to send data)
                    - baud_rate (communication speed, default is 9600 bits/s)
                    - parity possible: None (default), True means even, False means odd
                    - data_bits (default is 8)
                    - stop_bits (default is 1)
        """
        # set baud rate
        dwf.FDwfDigitalUartRateSet(self.device_data.handle, ctypes.c_double(baud_rate))

        # set communication channels
        dwf.FDwfDigitalUartTxSet(self.device_data.handle, ctypes.c_int(self.tx))
        dwf.FDwfDigitalUartRxSet(self.device_data.handle, ctypes.c_int(self.rx))

        # set data bit count
        dwf.FDwfDigitalUartBitsSet(self.device_data.handle, ctypes.c_int(data_bits))

        # set parity bit requirements
        if parity == True:
            parity = 2
        elif parity == False:
            parity = 1
        else:
            parity = 0
        dwf.FDwfDigitalUartParitySet(self.device_data.handle, ctypes.c_int(parity))

        # set stop bit count
        dwf.FDwfDigitalUartStopSet(self.device_data.handle, ctypes.c_double(stop_bits))

        # initialize channels with idle levels

        # dummy read
        dummy_buffer = ctypes.create_string_buffer(0)
        dummy_buffer = ctypes.c_int(0)
        dummy_parity_flag = ctypes.c_int(0)
        dwf.FDwfDigitalUartRx(
            self.device_data.handle,
            dummy_buffer,
            ctypes.c_int(0),
            ctypes.byref(dummy_buffer),
            ctypes.byref(dummy_parity_flag),
        )

        # dummy write
        dwf.FDwfDigitalUartTx(self.device_data.handle, dummy_buffer, ctypes.c_int(0))
        return

    def read_uart(self):
        """
        receives data from UART

        parameters: - device data
        return:     - integer list containing the received bytes
                    - error message or empty string
        """
        # variable to store results
        # error = ""
        # rx_data = []

        # create empty string buffer
        data = create_string_buffer(8193)

        # character counter
        count = ctypes.c_int(0)

        # parity flag
        parity_flag = ctypes.c_int(0)

        # read up to 8k characters
        dwf.FDwfDigitalUartRx(
            self.device_data.handle,
            data,
            ctypes.c_int(ctypes.sizeof(data) - 1),
            ctypes.byref(count),
            ctypes.byref(parity_flag),
        )

        # append current data chunks
        # for index in range(0, count.value):
        #     rx_data.append(int(data[index]))

        # ensure data integrity
        # while count.value > 0:
        #     # create empty string buffer
        #     data = (ctypes.c_ubyte * 8193)()

        #     # character counter
        #     count = ctypes.c_int(0)

        #     # parity flag
        #     parity_flag= ctypes.c_int(0)

        #     # read up to 8k characters
        #     dwf.FDwfDigitalUartRx(self.device_data.handle, data, ctypes.c_int(ctypes.sizeof(data)-1), ctypes.byref(count), ctypes.byref(parity_flag))
        #     # append current data chunks
        #     # for index in range(0, count.value):
        #     #     rx_data.append(int(data[index]))

        #     # check for not acknowledged
        #     if error == "":
        #         if parity_flag.value < 0:
        #             error = "Buffer overflow"
        #         elif parity_flag.value > 0:
        #             error = "Parity error: index {}".format(parity_flag.value)
        if count.value > 0:
            return data, count
        else:
            return None, count

    def write(self, data):
        """
        send data through UART

        parameters: - data of type string, int, or list of characters/integers
        """
        # cast data
        if type(data) == int:
            data = "".join(chr(data))
        elif type(data) == list:
            data = "".join(chr(element) for element in data)

        # encode the string into a string buffer
        data = ctypes.create_string_buffer(data.encode("UTF-8"))

        # send text, trim zero ending
        dwf.FDwfDigitalUartTx(
            self.device_data.handle, data, ctypes.c_int(ctypes.sizeof(data) - 1)
        )
        return

    def close(self):
        # dwf.FDwfDeviceClose(self.device_data.handle)
        # device.open(self.device_data.handle)
        # dwf.FDwfDigitalUartReset(self.device_data.handle)
        dwf.FDwfDigitalOutReset(self.device_data.handle)


# class SPI:
#     def __init__(self, device_data, rw_mode="r", data=[]):
#         self.device_data = device_data
#         self.cs = 33
#         self.sck = 32
#         self.miso = 35
#         self.mosi = 34
#         self.clk_freq = 1e06
#         self.mode = 0
#         self.order = True
#         self.data = data
#         self.rw_mode = rw_mode

#     def enabled(self):
#         csb = self.device_data.dio_map[self.cs]

#         while csb.get_value():
#             pass

#         print("CSB is low")

#         return True

#     def clk_trig(self):
#         clk = self.device_data.dio_map[self.sck]
#         if self.rw_mode == "r":
#             while not clk.get_value():
#                 pass
#             # print("clk is high")
#             self.read_data()
#             while clk.get_value():
#                 pass
#             # print("clk is low")
#         if self.rw_mode == "w":
#             while clk.get_value():
#                 pass
#             self.write_data()
#             while not clk.get_value():
#                 pass

#     def read_data(self):
#         input = self.device_data.dio_map[self.miso]
#         if input.get_value() == True:
#             self.data.append(1)
#         elif input.get_value() == False:
#             self.data.append(0)
#         print(self.data)

#     def write_data(self):
#         input = self.device_data.dio_map[self.mosi]
#         input.set_state(True)
#         input.set_value(self.data.pop(0))


class SPI:
    def __init__(self, device_data, rw_mode="r", data=[]):
        self.device_data = device_data
        self.cs = 11
        self.sck = 10
        self.miso = 13
        self.mosi = 12
        self.clk_frequency = 151
        self.mode = 0
        self.order = True
        self.data = data
        self.rw_mode = rw_mode

    def open(self):
        """
        initializes SPI communication
        parameters: - device data
                    - cs (DIO line used for chip select)
                    - sck (DIO line used for serial clock)
                    - miso (DIO line used for master in - slave out, optional)
                    - mosi (DIO line used for master out - slave in, optional)
                    - frequency (communication frequency in Hz, default is 1MHz)
                    - mode (SPI mode: 0: CPOL=0, CPHA=0; 1: CPOL-0, CPHA=1; 2: CPOL=1, CPHA=0; 3: CPOL=1, CPHA=1)
                    - order (endianness, True means MSB first - default, False means LSB first)
        """
        # set the clock frequency
        dwf.FDwfDigitalSpiFrequencySet(
            self.device_data.handle, ctypes.c_double(self.clk_frequency)
        )

        # set the clock pin
        dwf.FDwfDigitalSpiClockSet(self.device_data.handle, ctypes.c_int(self.sck))

        if self.mosi != None:
            # set the mosi pin
            dwf.FDwfDigitalSpiDataSet(
                self.device_data.handle, ctypes.c_int(0), ctypes.c_int(self.mosi)
            )

            # set the initial state
            dwf.FDwfDigitalSpiIdleSet(
                self.device_data.handle, ctypes.c_int(0), constants.DwfDigitalOutIdleZet
            )

        if self.miso != None:
            # set the miso pin
            dwf.FDwfDigitalSpiDataSet(
                self.device_data.handle, ctypes.c_int(1), ctypes.c_int(self.miso)
            )

            # set the initial state
            dwf.FDwfDigitalSpiIdleSet(
                self.device_data.handle, ctypes.c_int(1), constants.DwfDigitalOutIdleZet
            )

        # set the SPI mode
        dwf.FDwfDigitalSpiModeSet(self.device_data.handle, ctypes.c_int(self.mode))

        # set endianness
        if self.order:
            # MSB first
            dwf.FDwfDigitalSpiOrderSet(self.device_data.handle, ctypes.c_int(1))
        else:
            # LSB first
            dwf.FDwfDigitalSpiOrderSet(self.device_data.handle, ctypes.c_int(0))

        # set the cs pin HIGH
        dwf.FDwfDigitalSpiSelect(
            self.device_data.handle, ctypes.c_int(self.cs), ctypes.c_int(1)
        )

        # dummy write
        dwf.FDwfDigitalSpiWriteOne(
            self.device_data.handle, ctypes.c_int(1), ctypes.c_int(0), ctypes.c_int(0)
        )
        return

    def read(self, count):
        """
        receives data from SPI
        parameters: - device data
                    - count (number of bytes to receive)
                    - chip select line number
        return:     - integer list containing the received bytes
        """
        # enable the chip select line
        # dwf.FDwfDigitalSpiSelect(
        #     self.device_data.handle, ctypes.c_int(self.cs), ctypes.c_int(0)
        # )
        if dwf.FDwfDigitalInTriggerSet(
            self.device_data.handle,
            ctypes.c_int(0),
            ctypes.c_int(0),
            ctypes.c_int((1 << self.sck) | (1 << self.cs)),
            ctypes.c_int(0),
        ):
            # create buffer to store data
            buffer = (ctypes.c_ubyte * count)()

            # read array of 8 bit elements
            dwf.FDwfDigitalSpiRead(
                self.device_data.handle,
                ctypes.c_int(1),
                ctypes.c_int(8),
                buffer,
                ctypes.c_int(len(buffer)),
            )

            # disable the chip select line
            # dwf.FDwfDigitalSpiSelect(
            #     self.device_data.handle, ctypes.c_int(self.cs), ctypes.c_int(1)
            # )

            # decode data
            data = [int(element) for element in buffer]
            return data

    def write(self):
        """
        send data through SPI
        parameters: - device data
                    - data of type string, int, or list of characters/integers
                    - chip select line number
        """
        # cast data
        if type(data) == int:
            data = "".join(chr(data))
        elif type(data) == list:
            data = "".join(chr(element) for element in data)

        # enable the chip select line
        dwf.FDwfDigitalSpiSelect(
            self.device_data.handle, ctypes.c_int(self.cs), ctypes.c_int(0)
        )

        # create buffer to write
        data = bytes(data, "utf-8")
        buffer = (ctypes.c_ubyte * len(data))()
        for index in range(0, len(buffer)):
            buffer[index] = ctypes.c_ubyte(data[index])

        # write array of 8 bit elements
        dwf.FDwfDigitalSpiWrite(
            self.device_data.handle,
            ctypes.c_int(1),
            ctypes.c_int(8),
            buffer,
            ctypes.c_int(len(buffer)),
        )

        # disable the chip select line
        dwf.FDwfDigitalSpiSelect(
            self.device_data.handle, ctypes.c_int(self.cs), ctypes.c_int(1)
        )
        return

    def close(self):
        """
        reset the spi interface
        """
        dwf.FDwfDigitalSpiReset(self.device_data.handle)
        return
    
class LogicAnalyzer:
    def __init__(self, device_data):
        self.device_data = device_data
        self.sampling_frequency = 100e06
        self.buffer_size = 8
    
    def open(self):
        """
            initialize the logic analyzer
            parameters: - device data
                        - sampling frequency in Hz, default is 100MHz
                        - buffer size, default is 4096
        """
        # get internal clock frequency
        internal_frequency = ctypes.c_double()
        dwf.FDwfDigitalInInternalClockInfo(self.device_data.handle, ctypes.byref(internal_frequency))
    
        # set clock frequency divider (needed for lower frequency input signals)
        dwf.FDwfDigitalInDividerSet(self.device_data.handle, ctypes.c_int(int(internal_frequency.value / self.sampling_frequency)))
    
        # set 16-bit sample format
        dwf.FDwfDigitalInSampleFormatSet(self.device_data.handle, ctypes.c_int(16))
    
        # set buffer size
        dwf.FDwfDigitalInBufferSizeSet(self.device_data.handle, ctypes.c_int(self.buffer_size))
        # self.sampling_frequency = self.sampling_frequency
        # self.buffer_size = self.buffer_size
        return

    def record(self, channel):
        """
            initialize the logic analyzer
            parameters: - device data
                        - channel - the selected DIO line number
            returns:    - buffer - a list with the recorded logic values
                        - time - a list with the time moments for each value in seconds (with the same index as "buffer")
        """
        # set up the instrument
        dwf.FDwfDigitalInConfigure(self.device_data.handle, ctypes.c_bool(False), ctypes.c_bool(True))
        time.sleep(0.10)
    
        # read data to an internal buffer
        while True:
            status = ctypes.c_byte()    # variable to store buffer status
            dwf.FDwfDigitalInStatus(self.device_data.handle, ctypes.c_bool(True), ctypes.byref(status))
    
            if status.value == constants.stsDone.value:
                # exit loop when finished
                break

        buffer = (ctypes.c_uint16 * self.buffer_size)()
        dwf.FDwfDigitalInStatusData(self.device_data.handle, buffer, ctypes.c_int(self.buffer_size))
    
        # convert buffer to list of lists of integers
        buffer = [int(element) for element in buffer]
        result = [[] for _ in range(16)]
        for point in buffer:
            for index in range(16):
                result[index].append(point & (1 << index))
    
        # calculate acquisition time
        # time = range(0, self.buffer_size)
        # time = [moment / self.sampling_frequency for moment in time]
    
        # get channel specific data
        buffer = result[channel]
        nSamples = len(buffer)
        fFrequency = 0
        pass_c = 2**channel
        for i in range(1, nSamples):
            if (buffer[i] == 0 and buffer[i-1] == pass_c):
                fFrequency = self.sampling_frequency / (i * 2)
                
        return fFrequency
    
    def close(self):
        """
            reset the instrument
        """
        dwf.FDwfDigitalInReset(self.device_data.handle)
        return


def count_pulses(packet_data):
    state = "zero"
    pulse_count = 0
    for bit in packet_data:
        if state == "zero":
            if bit is True:
                state = "one"
                pulse_count = pulse_count + 1
        elif state == "one":
            if bit is False:
                state = "zero"
    return pulse_count


def connect_devices(devices, dev1_sn, dev2_sn, dev3_sn):
    """connects devices based on their serial number

    Args:
        devices (list): all devices connected

    Returns:
        [type]: [description]
    """
    # dev1 --> 7DA
    # dev2 --> AA0
    if devices:
        for device_info in devices:
            if device_info.serial_number[-3:] == dev1_sn:
                device1_data = device_info
            elif device_info.serial_number[-3:] == dev2_sn:
                device2_data = device_info
            elif device_info.serial_number[-3:] == dev3_sn:
                device3_data = device_info
    else:
        logging.error(" No connected devices")
        sys.exit()
    return device1_data, device2_data, device3_data


# def test_send_packet(device1v8, device3v3):
#     timeout = time.time() + 50
#     powerup_sequence(device1v8, device3v3)
#     logging.info("   reset on channel 0 device 1")
#     reset(device1v8)
#     logging.info("   Flashing CPU")
#     flash("caravel_board/hex_files/send_packet.hex")
#     powerup_sequence(device1v8, device3v3)
#     device1v8.supply.set_voltage(1.8)
#     reset(device1v8)
#     gpio_mgmt = device1v8.dio_map["gpio_mgmt"]
#     for i in range(0, 7):
#         pulse_count = receive_packet(device1v8)
#         print(f"pulses: {pulse_count}")
