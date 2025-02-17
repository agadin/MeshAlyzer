#include <SPI.h>

// ADS1256 Commands
#define CMD_WAKEUP    0x00
#define CMD_RDATA     0x01
#define CMD_RDATAC    0x03
#define CMD_SDATAC    0x0F
#define CMD_RREG      0x10
#define CMD_WREG      0x50
#define CMD_SELFCAL   0xF0

// ADS1256 Registers
#define REG_STATUS    0x00
#define REG_MUX       0x01
#define REG_ADCON     0x02
#define REG_DRATE     0x03

// Data rate setting (100 SPS)
#define DRATE_100SPS  0xF0

// Pin assignments
const int DRDY_PIN = 7;  // Data Ready pin from ADS1256
const int CS_PIN   = 8;  // Chip Select pin for ADS1256

// Function to send a command to the ADS1256
void sendCommand(byte command) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(command);
  digitalWrite(CS_PIN, HIGH);
}

// Read a single register from the ADS1256
byte readRegister(byte reg) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(CMD_RREG | reg);
  SPI.transfer(0x00);  // Number of registers to read minus one (here, 0 for one register)
  byte result = SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);
  return result;
}

// Write a value to a single ADS1256 register
void writeRegister(byte reg, byte value) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(CMD_WREG | reg);
  SPI.transfer(0x00);  // Write one register
  SPI.transfer(value);
  digitalWrite(CS_PIN, HIGH);
}

// Wait for the DRDY pin to go low (indicating data is ready)
void waitForDRDY() {
  while (digitalRead(DRDY_PIN) == HIGH) {
    delay(1);
  }
}

// Read a 24-bit ADC value from the specified channel (0-7)
// The positive input is set to AINx and the negative input is AINCOM.
long readADC(byte channel) {
  waitForDRDY();

  // Configure the multiplexer: (channel << 4) sets AINx as positive, 0x08 sets AINCOM as negative
  writeRegister(REG_MUX, (channel << 4) | 0x08);

  // Wake up the ADC and request a single conversion
  sendCommand(CMD_WAKEUP);
  sendCommand(CMD_RDATA);

  // A brief delay (in microseconds) may be needed here according to the ADS1256 timing requirements
  delayMicroseconds(10);

  // Read 3 bytes of conversion data
  digitalWrite(CS_PIN, LOW);
  byte b1 = SPI.transfer(0x00);
  byte b2 = SPI.transfer(0x00);
  byte b3 = SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);

  // Combine the three bytes into a 24-bit value
  long result = ((long)b1 << 16) | ((long)b2 << 8) | b3;

  // Convert to signed 24-bit (two's complement)
  if (result & 0x800000) {
    result -= 0x1000000;
  }

  return result;
}

// Initialize and configure the ADS1256
void setupADS1256() {
  sendCommand(CMD_SDATAC);          // Stop continuous data read mode, if active
  writeRegister(REG_STATUS, 0x06);    // Enable auto-calibration (see datasheet for details)
  writeRegister(REG_ADCON, 0x00);     // Gain = 1, clock out disabled
  writeRegister(REG_DRATE, DRATE_100SPS); // Set data rate to 100 SPS
  sendCommand(CMD_SELFCAL);           // Start self-calibration
  delay(100);                         // Wait 100 ms for calibration to complete
}

void setup() {
  Serial.begin(115200);

  // Configure the ADS1256 control pins
  pinMode(DRDY_PIN, INPUT);
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH); // Ensure CS is high (device deselected)

  // Initialize SPI
  SPI.begin();
  // ADS1256 typically uses SPI mode 1 (CPOL = 0, CPHA = 1) at up to 1 MHz.
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE1));

  Serial.println("Initializing ADS1256...");
  setupADS1256();
}

void loop() {
  // Read ADC value from channel 0
  long value = readADC(0);

  // Convert the 24-bit ADC value to voltage.
  // Assuming a 5V reference and full-scale positive value of 0x7FFFFF (i.e. 2^23 - 1)
  float voltage = (float)value * 5.0 / 8388607.0;

  Serial.print("ADC Channel 0: ");
  Serial.print(value);
  Serial.print(" (");
  Serial.print(voltage, 5);
  Serial.println(" V)");

  delay(500);  // Delay 500 ms between readings
}
