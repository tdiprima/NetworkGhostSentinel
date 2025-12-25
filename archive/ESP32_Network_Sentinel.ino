/*
  ESP32 Network Sentinel
  =====================
  Monitors the local network for new devices by performing periodic ping sweeps.
  Whitelists known device IPs in EEPROM as JSON array.
  Alerts on new devices by blinking an LED and logging to Serial in JSON format.
  Auto-learns new devices after alerting (to reduce false positives over time).
  
  Hardware:
  - ESP32 dev board
  - LED connected to GPIO 2 (built-in on most boards)
  
  Libraries needed (install via Arduino IDE Library Manager or PlatformIO):
  - ESP32Ping by MattC (for ping functionality)
  - ArduinoJson by Benoit Blanchon (v6+)
  
  Usage:
  1. Update SSID and PASSWORD.
  2. Optionally edit initial known devices.
  3. Upload to ESP32.
  4. Open Serial Monitor at 115200 baud.
  5. To reset whitelist: Comment out loadKnownDevices() and re-upload, or manually clear EEPROM.
  
  Notes:
  - Scans /24 subnet based on own IP (e.g., 192.168.1.x).
  - Ping is synchronous; scan takes ~30-60 seconds.
  - No MAC address detection (ESP32 Arduino lacks easy ARP table access).
    MAC shown as "unknown" - extend with promiscuous mode/ARP sniffing if needed.
  - Legal: Only use on your own network.
  - Optimizations: Could parallelize pings or use ARP sniffing for production.
*/

#include <WiFi.h>
#include <ESP32Ping.h>
#include <EEPROM.h>
#include <ArduinoJson.h>
#include <vector>

const char* ssid = "YOUR_WIFI_SSID";       // Update with your WiFi SSID
const char* password = "YOUR_WIFI_PASSWORD"; // Update with your WiFi password

#define LED_PIN 2                    // Built-in LED on most ESP32 boards
#define EEPROM_SIZE 1024             // EEPROM size in bytes
#define SCAN_INTERVAL 300000UL       // Scan every 5 minutes (ms)
#define PING_COUNT 1                 // Number of pings per target
#define SCAN_DELAY 50                // Delay between pings (ms) to avoid flooding

String networkBase;                      // e.g., "192.168.1."
std::vector<String> knownDevices;        // In-RAM list of known IP strings
unsigned long lastScan = 0;

// Forward declarations
void loadKnownDevices();
void saveKnownDevices();
void performScan();
void alertNewDevice(const String& ip);

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Initialize EEPROM
  EEPROM.begin(EEPROM_SIZE);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  // Get network base (assumes /24 subnet)
  IPAddress localIP = WiFi.localIP();
  networkBase = localIP.toString().substring(0, localIP.toString().lastIndexOf('.') + 1);
  Serial.print("WiFi connected. Local IP: ");
  Serial.print(localIP);
  Serial.print(" | Scanning: ");
  Serial.println(networkBase);

  // Load known devices from EEPROM
  loadKnownDevices();

  // Seed initial known devices if empty (router, self, common)
  if (knownDevices.empty()) {
    knownDevices.push_back(networkBase + "1");  // Router/gateway
    knownDevices.push_back(localIP.toString()); // Self
    // Add more known IPs here, e.g.:
    // knownDevices.push_back(networkBase + "10"); // Laptop
    // knownDevices.push_back(networkBase + "50"); // Printer
    saveKnownDevices();
    Serial.println("Initialized default known devices.");
  } else {
    Serial.print("Loaded ");
    Serial.print(knownDevices.size());
    Serial.println(" known devices.");
  }

  Serial.println("Network Sentinel active. Scans every 5 min.");
  Serial.println("=====================================");
}

void loop() {
  if (millis() - lastScan >= SCAN_INTERVAL) {
    performScan();
    lastScan = millis();
  }
  delay(1000);  // Heartbeat delay
}

void performScan() {
  Serial.println("--- Starting network scan ---");
  std::vector<String> currentDevices;
  int aliveCount = 0;

  for (int i = 1; i <= 254; i++) {
    String targetStr = networkBase + String(i);
    IPAddress target;
    if (target.fromString(targetStr)) {
      // Ping the target (returns true if at least one reply)
      bool isAlive = Ping.ping(target, PING_COUNT);
      if (isAlive) {
        aliveCount++;
        currentDevices.push_back(targetStr);

        // Check against known devices
        auto it = std::find(knownDevices.begin(), knownDevices.end(), targetStr);
        if (it == knownDevices.end()) {
          Serial.print("*** NEW DEVICE DETECTED: ");
          Serial.println(targetStr);
          alertNewDevice(targetStr);
          // Auto-learn: add to known after alert
          knownDevices.push_back(targetStr);
          saveKnownDevices();
        }
      }
    }
    delay(SCAN_DELAY);  // Throttle to prevent network flood
  }

  Serial.print("Scan complete. Alive devices: ");
  Serial.print(aliveCount);
  Serial.print(" / 254");
  Serial.println();
  Serial.println("--- Scan end ---\n");
}

void alertNewDevice(const String& ip) {
  // Blink LED rapidly to alert (10 blinks)
  for (int j = 0; j < 10; j++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  // Structured JSON log to Serial (could extend to MQTT/SD/HTTP)
  DynamicJsonDocument doc(512);
  doc["event"]     = "new_device";
  doc["ip"]        = ip;
  doc["mac"]       = "unknown";  // TODO: Implement ARP sniffing for real MAC
  doc["timestamp"] = millis();
  doc["subnet"]    = networkBase;

  String logEntry;
  serializeJsonPretty(doc, logEntry);
  Serial.println("ALERT JSON:");
  Serial.println(logEntry);
  Serial.println();
}

void loadKnownDevices() {
  knownDevices.clear();
  char buffer[512];
  EEPROM.get(0, buffer);  // Read JSON into buffer (null-terminated)

  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, buffer);
  if (!error) {
    JsonArray arr = doc.as<JsonArray>();
    for (JsonVariant v : arr) {
      knownDevices.push_back(v.as<String>());
    }
  } else {
    Serial.print("EEPROM load failed: ");
    Serial.println(error.c_str());
  }
}

void saveKnownDevices() {
  DynamicJsonDocument doc(1024);
  JsonArray arr = doc.to<JsonArray>();
  for (const String& ip : knownDevices) {
    arr.add(ip);
  }

  char eepromData[512];
  serializeJson(doc, eepromData, sizeof(eepromData));
  EEPROM.put(0, eepromData);
  EEPROM.commit();
  Serial.print("Saved ");
  Serial.print(knownDevices.size());
  Serial.println(" known devices to EEPROM.");
}
