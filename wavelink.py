import sys
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QDoubleSpinBox, QPushButton, QGridLayout, QComboBox, QLineEdit, QWidget, QSpinBox, QTextEdit

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

        saved_value_options = ['Select', 'WR-75', 'WR-51', 'WR-42', 'WR-34', 'WR-28', 'Coax']
        self.saved_values_combo = QComboBox()
        self.saved_values_combo.addItems(saved_value_options)
        self.saved_values_combo.currentIndexChanged.connect(self.handle_saved_value_selection)

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
        self.spin_boxes = [QDoubleSpinBox() if label != "Power (dBm)" else QSpinBox() for label in input_labels]
        self.calibration_edit = QLineEdit()
        self.calibration_edit.setPlaceholderText('Enter calibration data')

        default_values = [9.9, 15.0, 1021, 1, -10]
        for idx, (label, spin_box, default_value) in enumerate(zip(input_labels, self.spin_boxes, default_values)):
            layout.addWidget(QLabel(label), idx + 2, 0)
            if label == "Points":
                spin_box = QSpinBox()
                spin_box.setMinimum(1)
                spin_box.setMaximum(100001)
            elif label == "Power (dBm)":
                spin_box.setMinimum(-80)
                spin_box.setMaximum(20)
            spin_box.setValue(default_value)
            layout.addWidget(spin_box, idx + 2, 1)

        layout.addWidget(QLabel("Calibration:"), len(input_labels) + 2, 0)
        layout.addWidget(self.calibration_edit, len(input_labels) + 2, 1, 1, 2)

        self.submit_button = QPushButton("Submit")
        layout.addWidget(self.submit_button, len(input_labels) + 3, 0, 1, 3)

        self.submit_button.clicked.connect(self.handle_submit)

        central_widget.setLayout(layout)

        self.saved_value_data = {
            'WR-75': [12.4, 18.0, 2048, 2, -5],
            'WR-51': [15.0, 26.5, 8192, 4, -8],
            'WR-42': [18.0, 33.0, 16384, 8, -12],
            'WR-34': [22.0, 50.0, 32768, 16, -15],
            'WR-28': [26.5, 40.0, 65536, 32, -18],
            'Coax': [1.0, 2.0, 256, 0.1, 0]
        }

    def handle_saved_value_selection(self, index):
        selected_value = self.saved_values_combo.currentText()
        if selected_value in self.saved_value_data:
            values = self.saved_value_data[selected_value]
            for spin_box, value in zip(self.spin_boxes, values):
                spin_box.setValue(value)

    def handle_submit(self):
        input_values = [spin_box.value() for spin_box in self.spin_boxes]
        ip_address = self.ip_address_edit.text()
        calibration_data = self.calibration_edit.text()
        
        if self.validate_ipv4(ip_address):
            # Do something with the input values, valid IP address, and calibration data
            print("Input Values:", input_values)
            print("IP Address:", ip_address)
            print("Calibration Data:", calibration_data)
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
