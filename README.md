
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
   ```bash
   pip install -r requirements.txt
   ```

3. Connect hardware components:
   - Link pressure sensors to ADCs as shown in the wiring diagram.
   - Ensure relays and valves are connected to the Raspberry Pi GPIO pins as specified.

4. Launch the application:
   ```bash
   python main.py
   ```

---

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