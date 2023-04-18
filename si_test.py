from caravel import Dio, Test
from io_config import Device, device, connect_devices, UART, SPI
import logging
import os
import csv
import sys
import time
from manifest import (
    TestDict,
    device1_sn,
    device2_sn,
)


def init_ad_ios(device1_data, device2_data):
    device1_dio_map = {
        "rstb": Dio(0, device1_data, True),
        "gpio_mgmt": Dio(1, device1_data),
        0: Dio(2, device1_data),
        1: Dio(3, device1_data),
        2: Dio(4, device1_data),
        3: Dio(5, device1_data),
        4: Dio(6, device1_data),
        5: Dio(7, device1_data),
        6: Dio(8, device1_data),
        7: Dio(9, device1_data),
        8: Dio(10, device1_data),
        9: Dio(11, device1_data),
        10: Dio(12, device1_data),
        11: Dio(13, device1_data),
        12: Dio(14, device1_data),
        13: Dio(15, device1_data),
    }

    device2_dio_map = {
        22: Dio(0, device2_data),
        23: Dio(1, device2_data),
        24: Dio(2, device2_data),
        25: Dio(3, device2_data),
        26: Dio(4, device2_data),
        27: Dio(5, device2_data),
        28: Dio(6, device2_data),
        29: Dio(7, device2_data),
        30: Dio(8, device2_data),
        31: Dio(9, device2_data),
        32: Dio(10, device2_data),
        33: Dio(11, device2_data),
        34: Dio(12, device2_data),
        35: Dio(13, device2_data),
        36: Dio(14, device2_data),
        37: Dio(15, device2_data),
    }

    # device3_dio_map = {
    #     14: Dio(2, device3_data),
    #     15: Dio(3, device3_data),
    #     16: Dio(4, device3_data),
    #     17: Dio(5, device3_data),
    #     18: Dio(6, device3_data),
    #     19: Dio(7, device3_data),
    #     20: Dio(8, device3_data),
    #     21: Dio(9, device3_data),
    # }

    return device1_dio_map, device2_dio_map


def process_data(test):
    phase = 0
    for passing in test.passing_criteria:
        pulse_count = test.receive_packet(250)
        if pulse_count == passing:
            print(f"pass phase {phase}")
            phase = phase + 1

        if pulse_count == 9:
            print(f"{test.test_name} test failed with {test.voltage}v supply!")
            return False

    if len(test.passing_criteria) == phase:
        print(f"{test.test_name} test Passed with {test.voltage}v supply!")
        return True


def process_uart(test, uart):
    uart.open()
    rgRX = ""
    timeout = time.time() + 50
    pulse_count = test.receive_packet(250)
    if pulse_count == 2:
        print("start UART transmission")
    while time.time() < timeout:
        uart_data, count = uart.read_uart()
        if uart_data:
            uart_data[count.value] = 0
            rgRX = rgRX + uart_data.value.decode()
            if test.passing_criteria[0] in rgRX:
                print(rgRX)
                break
    pulse_count = test.receive_packet(250)
    if pulse_count == 5:
        print("end UART transmission")
    for i in range(0, 3):
        pulse_count = test.receive_packet(250)
        if pulse_count == 3:
            print("end UART test")


def process_mem(test):
    phase = 0
    mem_size = 0
    while True:
        pulse_count = test.receive_packet(250)
        if pulse_count == 1:
            print("start test")
        if pulse_count == 5:
            print(f"passed mem size {mem_size}")
            mem_size = mem_size + 1
        if pulse_count == 3:
            if phase > 1:
                print("Test finished")
                return True
            else:
                phase = phase + 1
                print("end test")

        if pulse_count == 9:
            print(
                f"{test.test_name} test failed with {test.voltage}v supply, mem size {mem_size}"
            )
            return mem_size


def flash_test(test, hex_file, uart, uart_data, mem):
    test.apply_reset()
    test.powerup_sequence()
    test.flash(hex_file)
    test.release_reset()
    test.powerup_sequence()
    logging.info(f"   changing VCORE voltage to {test.voltage}v")
    test.device1v8.supply.set_voltage(test.voltage)
    test.reset()
    if uart:
        return process_uart(test, uart_data)
    elif mem:
        return process_mem(test)
    else:
        return process_data(test)


def exec_test(test, writer, hex_file, uart=False, uart_data=None, mem=False):
    results = flash_test(test, hex_file, uart, uart_data, mem)
    arr = [test.test_name, test.voltage, results]
    writer.writerow(arr)


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        logging.info("  Running:  caravel.py")
        # open multiple devices
        devices = device.open_devices()
        # connect devices using hardcoded serial numbers
        d1_sn = bytes(device1_sn, "utf-8")
        d2_sn = bytes(device2_sn, "utf-8")
        device1_data, device2_data = connect_devices(devices, d1_sn, d2_sn)

        logging.info("   Initializing I/Os for both devices")
        # Initializing I/Os
        device1_dio_map, device2_dio_map = init_ad_ios(device1_data, device2_data)
        # Initilizing devices
        device1 = Device(device1_data, 0, device1_dio_map)
        device2 = Device(device2_data, 1, device2_dio_map)
        # if device3_data:
        #     device3 = Device(device3_data, 2, device3_dio_map)
        # else:
        #     device3 = None

        test = Test(device1, device2)
        uart_data = UART(device1_data)
        spi = SPI(device1_data)

        csv_header = ["test_name", "voltage (v)", "Pass/Fail"]
        if os.path.exists("./results.csv"):
            os.remove("./results.csv")

        with open("results.csv", "a", encoding="UTF8") as f:
            writer = csv.writer(f)

            # write the header
            writer.writerow(csv_header)
            for t in TestDict:
                test.test_name = t["test_name"]
                test.passing_criteria = t["passing_criteria"]
                for v in t["voltage"]:
                    test.voltage = v
                    logging.info(f"  Running:  {test.test_name}")
                    if t["uart"]:
                        exec_test(test, writer, t["hex_file_path"], True, uart_data)
                    elif t["mem"]:
                        exec_test(test, writer, t["hex_file_path"], mem=True)
                    else:
                        exec_test(test, writer, t["hex_file_path"])
        test.close_devices()
        sys.exit(0)
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            test.close_devices()
            sys.exit(1)
        except SystemExit:
            test.close_devices()
            os._exit(1)
