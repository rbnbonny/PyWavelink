#######################################################################
# How to use:
# python3 vna_get_s2p.py myfile.s2p
#
#######################################################################
# For help:
# python3 vna_get_s2p.py -h
#
# or contact: tim.tuuva@alumni.epfl.ch
#
#######################################################################
# Required libraries:
#
# pip3 install pyvisa-py pandas argparse rsinstrument scikit-rf
#
#######################################################################

import time
import argparse
import skrf as rf
import pandas as pd
import pyvisa as visa
from RsInstrument import *
from datetime import datetime
import plotly.graph_objects as go
from matplotlib import pyplot as plt


class VNA():

    def __init__(self, ip):
        self.ip = ip

    def connect(self):
        self.Instrument = RsInstrument("TCPIP::" + self.ip + "::5025::SOCKET",
                                       False, False, "SelectVisa='socket'")

        try:

            # Confirm VISA package to be chosen
            print(f'VISA Manufacturer: {self.Instrument.visa_manufacturer}')
            # Timeout for VISA Read Operations
            self.Instrument.visa_timeout = 50000
            # Timeout for opc-synchronised operations                       
            self.Instrument.opc_timeout = 50000
            # Error check after each command, can be True or False                    
            self.Instrument.instrument_status_checking = True
            # Clear status register
            self.Instrument.clear_status()

        except Exception:
            print("Warning: Couldn't connect target")

    def close(self):
        """Close the VISA session"""
        self.Instrument.close()

    def comcheck(self):
        """Check communication with the device"""
        # Just knock on the door to see if instrument is present
        idnResponse = self.Instrument.query_str('*IDN?')
        time.sleep(1)
        print('Hello, I am ' + idnResponse)

    def configure(self, df):
        self.Instrument.write_str_with_opc('SYSTEM:DISPLAY:UPDATE ON')

        unit_dct = {"kHz": 1e3, "MHz": 1e6, "GHz": 1e9}
        for _, setting in df.iterrows():
            if(setting["parameter"] == "f::start"):
                min_f = float(setting["value"]) * unit_dct[setting["unit"]]
                f_unit = setting["unit"]

            elif(setting["parameter"] == "f::stop"):
                max_f = float(setting["value"]) * unit_dct[setting["unit"]]

            elif(setting["parameter"] == "nb_pts"):
                nb_points = float(setting["value"])

            elif(setting["parameter"] == "bandwidth"):
                bandwidth = float(setting["value"]) * unit_dct[setting["unit"]]

            elif(setting["parameter"] == "power"):
                power = float(setting["value"])

            elif(setting["parameter"] == "cal_name"):
                calib_fname = str(setting["value"])

        if(not df.empty):
            self.frequency_sweep(power, min_f, max_f, f_unit, nb_points, bandwidth)

            # Recall calibration file
            if(calib_fname != "None"):
                self.Instrument.write_str_with_opc("MMEM:LOAD:CORR 1, '" + calib_fname + "'")
        time.sleep(1)

    def frequency_sweep(self, power, min_f, max_f, unit, nb_points, bandwidth):
        self.Instrument.write_str_with_opc("SOUR:POW1 " + str(power))
        self.Instrument.write_str_with_opc("FREQ:STAR " + str(min_f) + ";*WAI")
        self.Instrument.write_str_with_opc("FREQ:STOP " + str(max_f) + ";*WAI")
        self.Instrument.write_str_with_opc("SWE:POIN " + str(nb_points))
        self.Instrument.write_str_with_opc("BAND " + str(bandwidth))

        '''self.Instrument.write_str_with_opc("SENS1:AVER:COUN 10; :AVER ON")'''

    def idle(self):
        self.Instrument.write_str_with_opc("OUTPut1:STATe OFF")
        self.Instrument.write_str_with_opc("OUTPut2:STATe OFF")

    def power_on(self):
        self.Instrument.write_str_with_opc("OUTPut1:STATe ON")
        self.Instrument.write_str_with_opc("OUTPut2:STATe ON")

    def power_off(self):
        self.Instrument.write_str_with_opc("OUTPut1:STATe OFF")
        self.Instrument.write_str_with_opc("OUTPut2:STATe OFF")

    def measure_setup(self):
        self.power_on()
        # Display trace on VNA
        self.Instrument.write_str_with_opc("CALCulate1:PARameter:SDEFine 'TRC1', 'S11'")
        self.Instrument.write_str_with_opc("CALCulate1:PARameter:SDEFine 'TRC2', 'S21'")
        self.Instrument.write_str_with_opc("CALCulate1:PARameter:SDEFine 'TRC3', 'S12'")
        self.Instrument.write_str_with_opc("CALCulate1:PARameter:SDEFine 'TRC4', 'S22'")
        self.Instrument.write_str_with_opc("CALCulate1:FORMat MLOGarithmic")

        self.Instrument.write_str_with_opc("DISPlay:WINDow1:STATe ON")
        self.Instrument.write_str_with_opc("DISPlay:WINDow1:TRACe1:FEED 'TRC1'")
        self.Instrument.write_str_with_opc("DISPlay:WINDow1:TRACe2:FEED 'TRC2'")
        self.Instrument.write_str_with_opc("DISPlay:WINDow1:TRACe3:FEED 'TRC3'")
        self.Instrument.write_str_with_opc("DISPlay:WINDow1:TRACe4:FEED 'TRC4'")

        self.Instrument.write_str_with_opc("INITiate1:IMMediate;*WAI")
        self.Instrument.write_str_with_opc("INITiate1:CONTinuous OFF")  # Single shot measure (freeze the screen)
        self.power_off()

    def saves2p(self, s2p_filename):
        """Save the measurement to a s2p file"""
        self.Instrument.write_str_with_opc(f'MMEMory:STORe:TRACe:PORTs 1, "{s2p_filename}", COMPlex, 1, 2')


    def fileget(self, s2p_filename):
        """Perform calibration with short element"""
        self.Instrument.read_file_from_instrument_to_pc(s2p_filename, s2p_filename)


def to_plotly(ax=None):
    '''
    converts a matplotlib plot to a inline plotly plot. 
    '''
    if ax is None:
        ax = plt.gca()
    
    lines = []
    for line in ax.get_lines():
        lines.append({'x': line.get_xdata(),
                      'y': line.get_ydata(),
                      'name': line.get_label(),
                      })
   
    
    layout = {'title':ax.get_title(),
              'xaxis':{'title':ax.get_xlabel()},
              'yaxis':{'title':ax.get_ylabel()}
              }

    plt.close('all')
    #return lines, layout
    fig = go.Figure(data=lines, layout=layout)
    fig.show()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='S param buster',
                                     description='Library to get s2p data from R&S VNA')

    parser.add_argument('filename')
    args = parser.parse_args()

    # Define parameters, value, unit for the VNA configuration
    # You can change the second or third column of this dataset to configure the VNA
    # Can be loaded from a csv file using pd.read_csv(...)
    lst_wr75 = [["f::start", "9.9", "GHz"],
              ["f::stop", "15.0", "GHz"],
              ["nb_pts", "1021", "-"],
              ["bandwidth", "1", "kHz"],
              ["power", "-10.0", "dBm"],
              ["cal_name", "WR75", ""]
              ]
    lst_wr51 = [["f::start", "14.5", "GHz"],
              ["f::stop", "22.0", "GHz"],
              ["nb_pts", "1501", "-"],
              ["bandwidth", "1", "kHz"],
              ["power", "-10.0", "dBm"],
              ["cal_name", "WR51", ""]
              ]
    lst_wr42 = [["f::start", "17.6", "GHz"],
              ["f::stop", "26.7", "GHz"],
              ["nb_pts", "1821", "-"],
              ["bandwidth", "1", "kHz"],
              ["power", "-10.0", "dBm"],
              ["cal_name", "WR42", ""]
              ]
    lst_wr34 = [["f::start", "21.7", "GHz"],
              ["f::stop", "33.0", "GHz"],
              ["nb_pts", "2261", "-"],
              ["bandwidth", "1", "kHz"],
              ["power", "-10.0", "dBm"],
              ["cal_name", "WR34", ""]
              ]
    lst_wr28 = [["f::start", "26.3", "GHz"],
              ["f::stop", "40.0", "GHz"],
              ["nb_pts", "2741", "-"],
              ["bandwidth", "1", "kHz"],
              ["power", "-10.0", "dBm"],
              ["cal_name", "WR28", ""]
              ]
    
    lst_coax = [["f::start", "2.0", "GHz"],
              ["f::stop", "6.0", "GHz"],
              ["nb_pts", "1001", "-"],
              ["bandwidth", "1", "kHz"],
              ["power", "-10.0", "dBm"],
              ["cal_name", "coaxcav", ""]
              ]
    
    df_lst = lst_wr75

    df_conf = pd.DataFrame(df_lst, columns=["parameter", "value", "unit"])
    print(df_conf)

    # Use the actual VNA IP here (I would recommend using static IP)
    # TODO: Can also be passed as an argument using argparse library (similar to filename)
    vna_ip_addr = "10.43.1.19"

    # Actual execution
    print("Connecting and configuring the VNA")
    vna = VNA(vna_ip_addr)
    vna.connect()
    vna.comcheck()
    vna.configure(df_conf)

    print("Measuring S parameters")
    vna.measure_setup()
    vna.saves2p(args.filename)
    vna.fileget(args.filename)
    vna.close()
    print("Done!")

    print("Plotting for example purpose")
    data = rf.Network(args.filename)
    data.plot_s_db()
    to_plotly()
