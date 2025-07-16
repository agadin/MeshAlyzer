
# MeshAlyzer Device
<div align="center">
  <img src="https://raw.githubusercontent.com/agadin/MeshAlyzer/refs/heads/main/img/teampicmesh.jpg" alt="MeshAlyzer Team Picture" width="450"/>
  <br>
  <img src="https://raw.githubusercontent.com/agadin/MeshAlyzer/refs/heads/main/img/UIoverview.png" alt="MeshAlyzer UI Overview" width="450"/>
</div>

## Table of Contents

* [Introduction](#introduction)  
* [Installation](#installation)  
* [Usage](#usage)  
* [Contributing](#contributing)  
* [License](#license)  
* [Contact](#contact)  
* [Acknowledgements](#acknowledgements)  

---

## Introduction

The **MeshAlyzer** is an advanced testing device designed to simulate realistic coughing forces and pressures on a porcine abdominal wall. It enables researchers and surgeons to evaluate hernia mesh materials under dynamic conditions, facilitating informed decisions for hernia repair procedures.  

### Key Features
- **Pressure Control System**: Integrated pressure sensors with ADCs for precise measurements. 
- **Valve System**: Two 3-position, 5-way valves controlled by four relays.  
- **User Interface**: Customizable testing protocols and real-time data visualization.  
- **Data Logging**: Continuous recording of test data for in-depth analysis.  
- **Tissue Simulation**: Mimics coughing pressures with interchangeable balloon materials.  

---

## Installation
The MeshAlyzer device requires a Raspberry Pi 5 or Raspberry Pi 3 for operation. Follow the instructions below to set up your device.

### Raspberry Pi 5 Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/MeshAlyzer.git
   cd MeshAlyzer
   ```

2. Install dependencies:
   ```bash
   sudo apt-get install python3-lgpio
   ```
3. Set up the virtual environment (optional but recommended):
   ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
   ```
4. Start the application:
   ```bash
   python main.py
   ```

5. Connect hardware components:
   - Link pressure sensors to ADCs as shown in the wiring diagram.
   - Ensure relays and valves are connected to the Raspberry Pi GPIO pins as specified.

6. Launch the application:
   ```bash
   python main.py
   ```
### Raspberry Pi 3 setup
1. Create automatic startupfile
Create a file called '/etc/systemd/system/pi3-sensor.service' with the following content :
```ini
[Unit]
Description=Sensor Data Sender Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/path/to/PressureSensorReader.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```
Then enable and start the service with:

```
sudo systemctl enable pi3-sensor.service
sudo systemctl start pi3-sensor.service
```

2. Run the script to test the sensor:
```bash
sudo nano /etc/systemd/system/spidev-load.service
```
add:
```ini
[Unit]
[Unit]
Description=Pressure Sensor Client
After=network.target

[Service]
ExecStartPre=/sbin/modprobe spidev
ExecStart=/usr/bin/python3 /home/lakelab/MeshAlyzer/PressureSensorReader_rasp3.py
Restart=always
User=lakelab
WorkingDirectory=/home/lakelab
StandardOutput=inherit
StandardError=inherit

[Install]
WantedBy=multi-user.target
```
Then enable and start the service with:
```bash
sudo systemctl daemon-reexec
sudo systemctl enable spidev-load.service
sudo systemctl start spidev-load.service
```

##
### ADC Setup
The MeshAlyzer uses the ADS1256 ADC for pressure sensing. Follow these steps to set it up:

1. wiring diagram
Connect the ADS1256 to the Raspberry Pi 3:
VCC → 5V
GND → GND
DIN (MOSI) → GPIO 10 (SPI0 MOSI)
DOUT (MISO) → GPIO 9 (SPI0 MISO)
SCLK → GPIO 11 (SPI0 SCLK)
CS (Chip Select) → GPIO 8 (SPI0 CE0)
DRDY (Data Ready) → GPIO 7
RESET → GPIO 22

2. Install the required library:
```bash
sudo apt-get install python3-lgpio
```


## Usage

1. **Setup**:
   - Place the porcine tissue sample on the testing platform.
   - Connect the device to a power source and ensure all components are operational.

2. **Run Tests**:
   - Open the user interface and select a protocol.
   - Start the simulation and observe the test in progress.

3. **Analyze Data**:
   - Access the recorded data logs for performance evaluation.
   - Use the insights to determine optimal mesh materials.

---

## Contributing

We welcome contributions to enhance the MeshAlyzer project!  

### How to Contribute
1. Fork the repository.
2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of your changes"
   ```
4. Push your branch and create a pull request:
   ```bash
   git push origin feature-name
   ```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or feedback, please contact:  
- **Cole Hanan**  
- **Alexander Gadin**  
- **Evan Maples**  

---

## Acknowledgments

We would like to thank:  
- Dr. Spencer Lake for his guidance and support.  
- The BME Department at Washington University in St. Louis for resources and assistance.  
- The Chemistry Machine Shop for their technical expertise.  
