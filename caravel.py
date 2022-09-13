import argparse
from WF_SDK import *  # import instruments
from WF_SDK.dmm import *
from power_supply import PowerSupply
import time
import subprocess
import sys
from ctypes import *
import logging
import csv
import os


def accurate_delay(delay):
    """Function to provide accurate time delay in millisecond"""
    _ = time.perf_counter() + delay / 1000
    while time.perf_counter() < _:
        pass


class Test:
    def __init__(
        self, device1v8, device3v3, deviced, test_name = None, passing_criteria = [], voltage=1.6, sram=1
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


    def receive_packet(self):
        unit = 1000
        ones = 0
        pulses = 0
        while self.gpio_mgmt.get_value() != False:
            pass
        state = "LOW"
        accurate_delay(12.5)
        for i in range(0, 30):
            accurate_delay(25)
            x = self.gpio_mgmt.get_value()
            if state == "LOW":
                if x == True:
                    state = "HI"
            elif state == "HI":
                if x == False:
                    state = "LOW"
                    ones = 0
                    pulses = pulses + 1
            if x == True:
                ones = ones + 1
            if ones > 3:
                break
        # print("A packet has been received!")
        return pulses

    def reset(self, duration=1):
        logging.info("   applying reset on channel 0 device 1")
        self.rstb.set_value(0)
        time.sleep(duration)
        self.rstb.set_value(1)
        time.sleep(duration)
        logging.info("   reset done")

    def flash(self, hex_file):
        subprocess.call(
            f"python3 caravel_board/firmware_vex/util/caravel_hkflash.py {hex_file}",
            shell=True,
        )

    def change_voltage(self):
        self.device1v8.supply.set_voltage(self.voltage)

    def exec_flashing(self):
        logging.info("   Flashing CPU")
        if self.sram == 1:
            self.flash(f"caravel_board/hex_files/sram/{self.test_name}.hex")
        else:
            self.flash(f"caravel_board/hex_files/dffram/{self.test_name}.hex")
        self.powerup_sequence()
        logging.info(f"   changing VCORE voltage to {self.voltage}v")
        self.device1v8.supply.set_voltage(self.voltage)
        self.reset()

    def powerup_sequence(self):
        self.device3v3.supply.turn_off()
        self.device1v8.supply.turn_off()
        time.sleep(1)
        logging.info("   Turning on VIO")
        self.device3v3.supply.turn_on()
        self.device3v3.supply.set_voltage(3.3)
        time.sleep(1)
        logging.info("   Turning on VCORE")
        self.device1v8.supply.turn_on()
        time.sleep(1)

    def turn_off_devices(self):
        self.device1v8.supply.turn_off()
        self.device3v3.supply.turn_off()
        self.deviced.supply.turn_off()

    def close_devices(self):
        self.device1v8.supply.turn_off()
        self.device3v3.supply.turn_off()
        self.deviced.supply.turn_off()
        device.close(self.device1v8)
        device.close(self.device3v3)
        device.close(self.deviced)


class Device:
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
        self.rx = 6
        self.tx = 5
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
        dwf.FDwfDigitalUartRx(self.device_data.handle, dummy_buffer, ctypes.c_int(0), ctypes.byref(dummy_buffer), ctypes.byref(dummy_parity_flag))
    
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
        error = ""
        rx_data = []
    
        # create empty string buffer
        data = (ctypes.c_ubyte * 8193)()
    
        # character counter
        count = ctypes.c_int(0)
    
        # parity flag
        parity_flag= ctypes.c_int(0)
    
        # read up to 8k characters
        dwf.FDwfDigitalUartRx(self.device_data.handle, data, ctypes.c_int(ctypes.sizeof(data)-1), ctypes.byref(count), ctypes.byref(parity_flag))
    
        # append current data chunks
        for index in range(0, count.value):
            rx_data.append(int(data[index]))
    
        # ensure data integrity
        while count.value > 0:
            # create empty string buffer
            data = (ctypes.c_ubyte * 8193)()
    
            # character counter
            count = ctypes.c_int(0)
    
            # parity flag
            parity_flag= ctypes.c_int(0)
    
            # read up to 8k characters
            dwf.FDwfDigitalUartRx(self.device_data.handle, data, ctypes.c_int(ctypes.sizeof(data)-1), ctypes.byref(count), ctypes.byref(parity_flag))
            # append current data chunks
            for index in range(0, count.value):
                rx_data.append(int(data[index]))
    
            # check for not acknowledged
            if error == "":
                if parity_flag.value < 0:
                    error = "Buffer overflow"
                elif parity_flag.value > 0:
                    error = "Parity error: index {}".format(parity_flag.value)
        return rx_data
    def write(self, data):
        """
            send data through UART
    
            parameters: - data of type string, int, or list of characters/integers
        """
        # cast data
        if type(data) == int:
            data = "".join(chr (data))
        elif type(data) == list:
            data = "".join(chr (element) for element in data)
    
        # encode the string into a string buffer
        data = ctypes.create_string_buffer(data.encode("UTF-8"))
    
        # send text, trim zero ending
        dwf.FDwfDigitalUartTx(self.device_data.handle, data, ctypes.c_int(ctypes.sizeof(data)-1))
        return

def send_pulse(io, period):
    io.set_value(1)
    time.sleep(period / 2)
    io.set_value(0)
    time.sleep(period / 2)


def send_packet(io, pulse_count, period, end_period):
    for i in range(pulse_count):
        print(f"sending pulse {i}")
        send_pulse(io, period)
        io.set_value(1)
        time.sleep(end_period)


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


def connect_devices(devices):
    if devices:
        for device_info in devices:
            if device_info.serial_number[-3:] == b"1F8":
                device1_data = device_info
            elif device_info.serial_number[-3:] == b"F19":
                device2_data = device_info
            elif device_info.serial_number[-3:] == b"B2C":
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
