import sys
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QDoubleSpinBox, QPushButton, QGridLayout, QComboBox, QLineEdit, QWidget, QSpinBox

from vna_get_s2p import VNA
import pandas as pd

class DataInputApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyWavelink')
        self.setGeometry(100, 100, 400, 500)  # Adjust window dimensions

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()

        saved_value_options = ['Select', 'WR-75',
                               'WR-51', 'WR-42', 'WR-34', 'WR-28', 'Coax']
        self.saved_values_combo = QComboBox()
        self.saved_values_combo.addItems(saved_value_options)
        self.saved_values_combo.currentIndexChanged.connect(
            self.handle_saved_value_selection)

        layout.addWidget(QLabel("Saved Value:"), 0, 0)
        layout.addWidget(self.saved_values_combo, 0, 1, 1, 2)

        self.ip_address_edit = QLineEdit()
        self.ip_address_edit.setText('10.43.1.19')
        self.ip_address_edit.setPlaceholderText('Enter a valid IPv4 address')

        layout.addWidget(QLabel("IP Address:"), 1, 0)
        layout.addWidget(self.ip_address_edit, 1, 1, 1, 2)

        input_labels = [
            "Start Frequency (GHz)",
            "Stop Frequency (GHz)",
            "Points",
            "Bandwidth (kHz)",
            "Power (dBm)",
            "Calibration"
        ]
        self.spin_boxes = [QDoubleSpinBox() if label not in (
            "Points", "Power (dBm)") else QSpinBox() for label in input_labels]
        self.calibration_edit = QLineEdit()
        self.calibration_edit.setPlaceholderText('Enter calibration data')

        for idx, (label, spin_box) in enumerate(zip(input_labels, self.spin_boxes)):
            layout.addWidget(QLabel(label), idx + 2, 0)
            if label == "Points":
                spin_box.setMinimum(1)
                spin_box.setMaximum(100001)
            elif label == "Power (dBm)":
                spin_box.setMinimum(-80)
                spin_box.setMaximum(20)
            layout.addWidget(spin_box, idx + 2, 1)

        layout.addWidget(QLabel("Calibration:"), len(input_labels) + 2, 0)
        layout.addWidget(self.calibration_edit, len(input_labels) + 2, 1, 1, 2)

        self.submit_button = QPushButton("Submit")
        layout.addWidget(self.submit_button, len(input_labels) + 3, 0, 1, 3)

        self.submit_button.clicked.connect(self.handle_submit)

        central_widget.setLayout(layout)

        self.saved_value_data = {
            'WR-75': [9.9, 15.0, 1021, 1, -10],
            'WR-51': [14.5, 22.0, 1501, 1, -10],
            'WR-42': [17.6, 26.7, 1821, 1, -10],
            'WR-34': [21.7, 33.0, 2261, 1, -10],
            'WR-28': [26.3, 40.0, 2741, 1, -10],
            'Coax': [2.0, 6.0, 1001, 1, -10]
        }

        self.calibration_data = {
            'WR-75': 'WR75',
            'WR-51': 'WR51',
            'WR-42': 'WR42',
            'WR-34': 'WR34',
            'WR-28': 'WR28',
            'Coax': 'coaxcav'
        }

    def handle_saved_value_selection(self, index):
        selected_value = self.saved_values_combo.currentText()
        if selected_value in self.saved_value_data:
            values = self.saved_value_data[selected_value]
            for idx, (spin_box, value) in enumerate(zip(self.spin_boxes, values)):
                spin_box.setValue(value)

            # Update the calibration text field if a calibration value exists for the selected option
            if selected_value in self.calibration_data:
                self.calibration_edit.setText(
                    self.calibration_data[selected_value])
            else:
                # Clear the text field if no calibration value is available
                self.calibration_edit.clear()

    def handle_submit(self):
        input_values = [spin_box.value() for spin_box in self.spin_boxes]
        ip_address = self.ip_address_edit.text()
        calibration_data = self.calibration_edit.text()

        if self.validate_ipv4(ip_address):
            # Create an instance of the VNA class and connect to the VNA
            vna = VNA(ip_address)
            vna.connect()

            # Prepare the configuration DataFrame based on the input values
            df_conf = pd.DataFrame([
                ["f::start", input_values[0], "GHz"],
                ["f::stop", input_values[1], "GHz"],
                ["nb_pts", input_values[2], "-"],
                ["bandwidth", input_values[3], "kHz"],
                ["power", input_values[4], "dBm"],
                ["cal_name", calibration_data if calibration_data else "None", ""]
            ], columns=["parameter", "value", "unit"])

            # Configure the VNA and perform measurements
            vna.comcheck()
            vna.configure(df_conf)
            vna.measure_setup()

            # Save and retrieve S-parameter data
            s2p_filename = "measurement.s2p"  # Change the filename as needed
            vna.saves2p(s2p_filename)
            vna.fileget(s2p_filename)

            # Close the connection to the VNA
            vna.close()

            print("Measurement and data retrieval complete.")
        else:
            print("Invalid IP Address:", ip_address)


    def validate_ipv4(self, ip_address):
        ipv4_pattern = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
        return ipv4_pattern.match(ip_address) is not None


def main():
    app = QApplication(sys.argv)
    window = DataInputApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
