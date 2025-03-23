
# MeshAlyzer Device

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

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/MeshAlyzer.git
   cd MeshAlyzer
   ```

2. Install dependencies:
Below is an updated README installation section that uses **lgpio** instead of **RPi.GPIO**. This version outlines the installation steps and highlights potential conflicts—especially if you’re also using libraries (like gpiozero) that normally expect RPi.GPIO.

---

# Installation

This guide details how to set up your Raspberry Pi environment to run the project’s Python scripts while using **lgpio** as your GPIO interface.

> **Note:**  
> Ensure that **RPi.GPIO** is not installed (or used) if you’re switching to **lgpio**. If you’ve previously installed RPi.GPIO, remove it or avoid importing it in your projects. When using gpiozero, you may need to set its pin factory to `lgpio` (see below).

## Prerequisites
- **Hardware:** Raspberry Pi running Raspberry Pi OS.
- **Network:** Active Internet connection.
- **Access:** Local terminal or SSH.
- **Tools:** Git (typically pre-installed on Raspberry Pi OS).

## 1. System Update

Update your package lists and upgrade installed packages:
```bash
sudo apt update && sudo apt upgrade -y
```

## 2. Installing System Packages

Install essential system-level packages:
```bash
# Install Python development tools and I2C utilities
sudo apt-get install python3-pip python3-dev i2c-tools

# Install pigpio for advanced GPIO control (required by some scripts)
sudo apt install pigpio

# Install lgpio (use this instead of RPi.GPIO)
sudo apt install python3-lgpio

# (Optional) Install OpenCV for image processing tasks
sudo apt install python3-opencv

# Ensure SPI support is enabled (if your project requires it)
sudo modprobe spidev
```

## 3. Setting Up a Python Virtual Environment

It is recommended to use a virtual environment for managing Python dependencies:
```bash
# Create a virtual environment named "myenv"
python3 -m venv myenv

# Activate the virtual environment
source myenv/bin/activate
```

## 4. Python Dependencies

Install the necessary Python libraries. **Do not install RPi.GPIO**—use lgpio for GPIO access instead:

```bash
# Install gpiozero (and tell it to use lgpio as the backend)
pip install gpiozero

# If gpiozero does not automatically detect lgpio, set the pin factory before running your scripts:
# export GPIOZERO_PIN_FACTORY=lgpio

# LED and Neopixel control
pip install rpi_ws281x
pip install adafruit-circuitpython-neopixel

# Adafruit Blinka (for CircuitPython compatibility on Raspberry Pi)
pip3 install --force-reinstall adafruit-blinka

# Character LCD library (if using LCD displays)
pip3 install adafruit-circuitpython-charlcd

# Serial communication
pip install pyserial

# Image processing and data visualization
pip install opencv-python matplotlib pillow pandas seaborn

# Additional utilities
pip install tkfontawesome libxslt libxml2 cairosvg

# GitHub API for interacting with GitHub
pip install PyGithub
```

If your project provides a `requirements.txt` file, you can install all dependencies at once:
```bash
pip install -r requirements.txt
```

## 5. Using lgpio with gpiozero

Since **gpiozero** defaults to RPi.GPIO, set the pin factory to **lgpio** if needed. You can do this by adding the following line to your shell or your project’s startup script:
```bash
export GPIOZERO_PIN_FACTORY=lgpio
```
This ensures that gpiozero uses **lgpio** for GPIO access.

## 6. Starting the pigpio Daemon

```bash
sudo pigpiod
```

## 6. Installing Adafruit Blinka
Download and run the Adafruit Blinka installer to ensure proper hardware support for CircuitPython libraries:

```bash
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py
```

## 7. Additional Configuration

- **Hardware Access:**  
  Allow low-level hardware access if required:
  ```bash
  sudo chmod 666 /dev/mem
  ```

- **Interface Settings:**  
  Use the Raspberry Pi configuration tool to enable additional interfaces (I2C, SPI, VNC, etc.):
  ```bash
  sudo raspi-config
  ```

## 8. Running the Application

After completing the installation and configuration steps, run your Python scripts:
```bash
python main.py
```

Keep your project code up-to-date by using:
```bash
git pull
```

---


### ADC Setup

1. wiring diagram
Connect the ADS1256 to the Raspberry Pi:
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

## Acknowledgements

We would like to thank:  
- Dr. Spencer Lake for his guidance and support.  
- The BME Department at Washington University in St. Louis for resources and assistance.  
- The Chemistry Machine Shop for their technical expertise.  

--- 

Let me know if you'd like further edits or additional sections!