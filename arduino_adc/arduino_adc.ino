#include <SPI.h>
#include <digitalWriteFast.h>  // Ensure this library is installed!

// **ADS1256 Pin Definitions (Make sure these match your wiring!)**
#define ADS_RST_PIN    9   // ADS1256 Reset
#define ADS_RDY_PIN    2   // ADS1256 Data Ready (must be an interrupt pin)
#define ADS_CS_PIN     10  // ADS1256 Chip Select

// **SPI Configuration**
#define SPI_SPEED 2500000

// **ADS1256 Commands**
#define CMD_RDATA   0x01  // Read Data Once
#define CMD_SDATAC  0x0F  // Stop Continuous Read
#define CMD_RREG    0x10  // Read Register
#define CMD_WREG    0x50  // Write Register
#define CMD_RESET   0xFE  // Reset Device

// **ADS1256 Registers**
#define REG_STATUS  0x00
#define REG_MUX     0x01
#define REG_ADCON   0x02
#define REG_DRATE   0x03

// **ADC Constants**
double resolution = 8388608.;  // 2^23-1
double Gain = 1.;              // Set to match ADC gain settings
double vRef = 5.0;             // Reference voltage (adjust if using external VREF)
double bitToVolt;              // Conversion factor calculated in setup

// **Pressure Sensor Mapping (Modify for your specific sensor range)**
#define PRESSURE_MIN 0.5   // 0.5V at 0 PSI
#define PRESSURE_MAX 4.5   // 4.5V at max PSI
#define PRESSURE_RANGE 150 // 150 PSI sensor (adjust as needed)

// **Function to Send SPI Command**
void sendCommand(byte command) {
  digitalWriteFast(ADS_CS_PIN, LOW);
  SPI.transfer(command);
  digitalWriteFast(ADS_CS_PIN, HIGH);
}

// **Function to Write to a Register**
void writeRegister(byte reg, byte value) {
  digitalWriteFast(ADS_CS_PIN, LOW);
  SPI.transfer(CMD_WREG | reg);
  SPI.transfer(0x00);  // Write only one register
  SPI.transfer(value);
  digitalWriteFast(ADS_CS_PIN, HIGH);
}

// **Function to Read a Register**
byte readRegister(byte reg) {
  digitalWriteFast(ADS_CS_PIN, LOW);
  SPI.transfer(CMD_RREG | reg);
  SPI.transfer(0x00);  // Read only one register
  byte result = SPI.transfer(0x00);
  digitalWriteFast(ADS_CS_PIN, HIGH);
  return result;
}

// **Function to Wait for Data Ready**
void waitForDRDY() {
  while (digitalReadFast(ADS_RDY_PIN) == HIGH);
}

// **Function to Read ADC Value**
long readADC() {
  waitForDRDY();
  sendCommand(CMD_RDATA);
  delayMicroseconds(10);

  digitalWriteFast(ADS_CS_PIN, LOW);
  byte b1 = SPI.transfer(0x00);
  byte b2 = SPI.transfer(0x00);
  byte b3 = SPI.transfer(0x00);
  digitalWriteFast(ADS_CS_PIN, HIGH);

  long result = ((long)b1 << 16) | ((long)b2 << 8) | b3;
  if (result & 0x800000) result -= 0x1000000;

  return result;
}

// **Function to Initialize ADS1256**
void initADS() {
  sendCommand(CMD_RESET);
  delay(10);

  sendCommand(CMD_SDATAC);
  delay(10);

  writeRegister(REG_MUX, (0x00 << 4) | 0x08);  // AIN0 vs AINCOM (single-ended)
  writeRegister(REG_ADCON, 0x00);  // Gain = 1
  writeRegister(REG_DRATE, 0xF0);  // Data rate = 100 SPS
  delay(100);
}

// **Arduino Setup**
void setup() {
  delay(1000);
  Serial.begin(115200);
  Serial.println("Booting ADS1256...");

  // Initialize ADS1256 Pins
  pinMode(ADS_CS_PIN, OUTPUT);
  pinMode(ADS_RDY_PIN, INPUT);
  pinMode(ADS_RST_PIN, OUTPUT);

  // Initialize SPI
  SPI.begin();
  SPI.beginTransaction(SPISettings(SPI_SPEED, MSBFIRST, SPI_MODE1));

  // Initialize ADS1256
  initADS();
  Serial.println("ADS1256 Initialized!");

  // Verify ADS1256 STATUS Register
  byte status = readRegister(REG_STATUS);
  Serial.print("ADS1256 STATUS REGISTER: 0x");
  Serial.println(status, HEX);
  
  // Calculate ADC to Voltage Conversion Factor
  bitToVolt = vRef / resolution;
}

// **Main Loop: Read and Display Pressure Sensor Values**
void loop() {
  long adc_value = readADC();
  float voltage = (float)adc_value * bitToVolt;

  // Convert voltage to pressure (linear scaling)
  float pressure = ((voltage - PRESSURE_MIN) / (PRESSURE_MAX - PRESSURE_MIN)) * PRESSURE_RANGE;

  Serial.print("ADC: "); Serial.print(adc_value);
  Serial.print(" | Voltage: "); Serial.print(voltage, 5);
  Serial.print(" V | Pressure: "); Serial.print(pressure, 2);
  Serial.println(" PSI");

  delay(500);
}
