// ================== Core ESP32 Local Logic ==================
#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// ====== Pin Configs (AI-Thinker ESP32-CAM default) ======
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ====== Ultrasonic pins ======
#define TRIG_PIN  12
#define ECHO_PIN  13

// ====== Motors & LED ======
#define LED_PIN   2      // braking indicator
#define MOTOR_A1  25     // forward
#define MOTOR_A2  26     // reverse
#define STEER_L   14     // steer left
#define STEER_R   27     // steer right

// ====== Config ======
#define BRAKE_DISTANCE 20   // cm threshold for braking

// WiFi credentials
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";

// Cloud endpoint (Flask / Firebase / etc.)
String serverUrl = "https://bvcantcode-edgelords.hf.space/predict";

// --------------------- Camera Init ---------------------
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_QVGA;  
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_CIF;   
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    while (true) delay(1000);
  }
  Serial.println("Camera ready.");
}

// --------------------- Ultrasonic ---------------------
long getDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); 
  if (duration == 0) return -1;
  return duration * 0.034 / 2;
}

// --------------------- Motor Control ---------------------
void motorForward() {
  digitalWrite(MOTOR_A1, HIGH);
  digitalWrite(MOTOR_A2, LOW);
}

void motorReverse() {
  digitalWrite(MOTOR_A1, LOW);
  digitalWrite(MOTOR_A2, HIGH);
}

void motorStop() {
  digitalWrite(MOTOR_A1, LOW);
  digitalWrite(MOTOR_A2, LOW);
}

void steerLeft() {
  digitalWrite(STEER_L, HIGH);
  digitalWrite(STEER_R, LOW);
}

void steerRight() {
  digitalWrite(STEER_L, LOW);
  digitalWrite(STEER_R, HIGH);
}

void steerStraight() {
  digitalWrite(STEER_L, LOW);
  digitalWrite(STEER_R, LOW);
}

// ==================  Cloud Upload Logic ==================

// Upload frame to server and get steering command
String sendFrameToServer(camera_fb_t * fb) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected.");
    return "FORWARD"; // fallback
  }
  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  http.begin(client, serverUrl);  
  http.addHeader("Content-Type", "image/jpeg");
  
  int httpResponseCode = http.POST(fb->buf, fb->len);

  String result = "FORWARD"; // default
  if (httpResponseCode > 0) {
    result = http.getString();
    result.trim();
    Serial.printf("Server response: %s\n", result.c_str());
  } else {
    Serial.printf("Error code: %d\n", httpResponseCode);
  }

  http.end();
  return result;
}

// ================== SETUP ==================
void setup() {
  Serial.begin(115200);
  delay(2000);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTOR_A1, OUTPUT);
  pinMode(MOTOR_A2, OUTPUT);
  pinMode(STEER_L, OUTPUT);
  pinMode(STEER_R, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  motorStop();
  steerStraight();

  initCamera();

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi.");
  Serial.println("System ready.");
}

// ================== LOOP ==================
void loop() {
  // 1. Safety check with ultrasonic
  long distance = getDistanceCM();
  if (distance > 0) Serial.printf("Distance: %ld cm\n", distance);

  if (distance > 0 && distance <= BRAKE_DISTANCE) {
    Serial.println("Obstacle too close -> braking.");
    digitalWrite(LED_PIN, HIGH);
    motorReverse();
    delay(400);
    motorStop();
    delay(500);
    return; 
  }

  // 2. Capture camera frame
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    motorStop();
    delay(200);
    return;
  }

  // 3. Send to cloud CNN model
  String command = sendFrameToServer(fb);
  esp_camera_fb_return(fb);

  // 4. Actuate motors based on CNN response
  digitalWrite(LED_PIN, LOW);
  if (command == "LEFT") {
    steerLeft();
    motorForward();
  } else if (command == "RIGHT") {
    steerRight();
    motorForward();
  } else { // FORWARD
    steerStraight();
    motorForward();
  }

  delay(200);
}
