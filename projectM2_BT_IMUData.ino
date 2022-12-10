#include <ArduinoBLE.h>
#include <Arduino_LSM6DS3.h>

#define BLE_DEVICE_NAME "ZSR_Nano33Iot"
#define BLE_LOCAL_NAME "ZSR_Nano33Iot"

#define BLE_UUID_ACCELEROMETER_SERVICE "1101"
#define BLE_UUID_ACCELEROMETER_X "2101"
#define BLE_UUID_ACCELEROMETER_Y "2102"
#define BLE_UUID_ACCELEROMETER_Z "2103"
#define BLE_UUID_GYROSCOPE_X "2104"
#define BLE_UUID_GYROSCOPE_Y "2105"
#define BLE_UUID_GYROSCOPE_Z "2106"

BLEService IMUService(BLE_UUID_ACCELEROMETER_SERVICE);
BLEFloatCharacteristic accelerometerX(BLE_UUID_ACCELEROMETER_X, BLERead | BLENotify);
BLEFloatCharacteristic accelerometerY(BLE_UUID_ACCELEROMETER_Y, BLERead | BLENotify);
BLEFloatCharacteristic accelerometerZ(BLE_UUID_ACCELEROMETER_Z, BLERead | BLENotify);
BLEFloatCharacteristic gyroscopeX(BLE_UUID_GYROSCOPE_X, BLERead | BLENotify);
BLEFloatCharacteristic gyroscopeY(BLE_UUID_GYROSCOPE_Y, BLERead | BLENotify);
BLEFloatCharacteristic gyroscopeZ(BLE_UUID_GYROSCOPE_Z, BLERead | BLENotify);

// Init IMU variables
float ax, ay, az;
float gx, gy, gz;

// ---------------------------------------------------------------------------------------

void setup() {

  // LED to indicate if connected(on) or disconnected(off)
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(9600);
  while (!Serial);

  // begin initialization
  if (!BLE.begin()) {
    Serial.println("starting Bluetooth® Low Energy failed!");
    while (1);
  }
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
  
  Serial.print("Accelerometer sample rate = ");
  Serial.print(IMU.accelerationSampleRate());
  Serial.println("Hz");

  // set advertised local name and service UUID:
  BLE.setDeviceName(BLE_DEVICE_NAME);
  BLE.setLocalName(BLE_LOCAL_NAME);
  BLE.setAdvertisedService(IMUService);

  // add the characteristic to the service
  IMUService.addCharacteristic(accelerometerX);
  IMUService.addCharacteristic(accelerometerY);
  IMUService.addCharacteristic(accelerometerZ);
  IMUService.addCharacteristic(gyroscopeX);
  IMUService.addCharacteristic(gyroscopeY);
  IMUService.addCharacteristic(gyroscopeZ);

  // add service
  BLE.addService(IMUService);

  // set initial values for characteristics
  accelerometerX.writeValue(0);
  accelerometerY.writeValue(0);
  accelerometerZ.writeValue(0);
  gyroscopeX.writeValue(0);
  gyroscopeY.writeValue(0);
  gyroscopeZ.writeValue(0);

  // start advertising device on BLE network
  BLE.advertise();

  Serial.println("BLE IMU Peripheral");
}
// --------------------------------------------------------------------------------------
void loop() {
  // listen for BLE peripherals to connect:
  BLEDevice central = BLE.central();
  

  // if a central is connected to peripheral:
  if (central) {
    // turn led on
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.print("Connected to central: ");
    // print the central's MAC address:
    Serial.println(central.address());
    // Serial.println("\n");
    Serial.print("Periperal address : ");
    Serial.print(BLE.address());


    // while the central is still connected to peripheral:
    while (central.connected()) {

      // read IMU values
      if (IMU.accelerationAvailable()) {
        IMU.readAcceleration(ax, ay, az);
      }
      if (IMU.gyroscopeAvailable()) {
        IMU.readGyroscope(gx, gy, gz);
      }
      // Write IMU values into BT service variables
      // BT Service variables are transmitted to master device (LightBlue App | Phone)
      accelerometerX.writeValue(ax);
      accelerometerY.writeValue(ay);
      accelerometerZ.writeValue(az);
      gyroscopeX.writeValue(gx);
      gyroscopeY.writeValue(gy);
      gyroscopeZ.writeValue(gz);            
    }

    // when the central disconnects, print it out:
    digitalWrite(LED_BUILTIN, LOW);
    Serial.print(F("Disconnected from central: "));
    Serial.println(central.address());
  }
}