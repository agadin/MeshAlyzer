#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import ADS1263
import config

REF = 5.08  # Modify according to actual voltage

# ADC1 test part
TEST_ADC1 = True
# ADC2 test part
TEST_ADC2 = False
# ADC1 rate test part
TEST_ADC1_RATE = False
# RTD test part
TEST_RTD = False

try:
    ADC = ADS1263.ADS1263()

    # The faster the rate, the less stable the conversion;
    # choose an appropriate digital filter (see REG_MODE1) if needed.
    if ADC.ADS1263_init_ADC1('ADS1263_400SPS') == -1:
        exit()
    ADC.ADS1263_SetMode(0)  # 0 for singleChannel, 1 for diffChannel

    # Uncomment to test DAC functions if required:
    # ADC.ADS1263_DAC_Test(1, 1)      # Open IN6
    # ADC.ADS1263_DAC_Test(0, 1)      # Open IN7

    if TEST_ADC1:  # ADC1 Test
        channelList = [0, 1, 2, 3, 4]  # The channel must be less than 10
        while True:
            ADC_Value = ADC.ADS1263_GetAll(channelList)
            for i in channelList:
                if ADC_Value[i] >> 31 == 1:
                    print("ADC1 IN%d = -%lf" % (i, (REF * 2 - ADC_Value[i] * REF / 0x80000000)))
                else:
                    print("ADC1 IN%d = %lf" % (i, (ADC_Value[i] * REF / 0x7fffffff)))
            for i in channelList:
                print("\33[2A")

    elif TEST_ADC2:
        if ADC.ADS1263_init_ADC2('ADS1263_ADC2_400SPS') == -1:
            exit()
        while True:
            ADC_Value = ADC.ADS1263_GetAll_ADC2()
            for i in range(10):
                if ADC_Value[i] >> 23 == 1:
                    print("ADC2 IN%d = -%lf" % (i, (REF * 2 - ADC_Value[i] * REF / 0x800000)))
                else:
                    print("ADC2 IN%d = %lf" % (i, (ADC_Value[i] * REF / 0x7fffff)))
            print("\33[11A")

    elif TEST_ADC1_RATE:  # Rate test
        time_start = time.time()
        ADC_Value = []
        isSingleChannel = True
        if isSingleChannel:
            while True:
                ADC_Value.append(ADC.ADS1263_GetChannalValue(0))
                if len(ADC_Value) == 5000:
                    time_end = time.time()
                    print(time_start, time_end)
                    print(time_end - time_start)
                    print('frequency = ', 5000 / (time_end - time_start))
                    break
        else:
            while True:
                ADC_Value.append(ADC.ADS1263_GetChannalValue(0))
                if len(ADC_Value) == 5000:
                    time_end = time.time()
                    print(time_start, time_end)
                    print(time_end - time_start)
                    print('frequency = ', 5000 / (time_end - time_start))
                    break

    elif TEST_RTD:  # RTD Test
        while True:
            ADC_Value = ADC.ADS1263_RTD_Test()
            RES = ADC_Value / 2147483647.0 * 2.0 * 2000.0  # 2000 Ohm sensor example
            print("RES is %lf" % RES)
            TEMP = (RES / 100.0 - 1.0) / 0.00385  # Example for a PT100 sensor
            print("TEMP is %lf" % TEMP)
            print("\33[3A")

    ADC.ADS1263_Exit()

except IOError as e:
    print(e)

except KeyboardInterrupt:
    print("ctrl + c:")
    print("Program end")
    ADC.ADS1263_Exit()
    exit()
