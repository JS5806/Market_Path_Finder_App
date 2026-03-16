/**
 * Market Path Finder - ESP32 ESL Controller
 *
 * [하드웨어 연동 담당: 이재상]
 *
 * 기능:
 *   1) WiFi 연결 → MQTT 브로커(라즈베리 파이) 접속
 *   2) mart/esl/update/<MAC> 토픽 구독 → JSON 메시지 수신
 *   3) E-Ink(전자잉크) 디스플레이에 상품명 + 가격 표시
 *   4) mart/esl/status/<MAC> 토픽으로 상태 보고
 *
 * 의존 라이브러리 (platformio.ini에 추가):
 *   - WiFi (ESP32 내장)
 *   - PubSubClient (MQTT)
 *   - ArduinoJson
 *   - GxEPD2 (E-Ink 디스플레이)
 *
 * Step Z에서 이재상 님이 실제 SPI 핀 연결 후 이 코드를 완성합니다.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
// #include <GxEPD2_BW.h>  // Step Z: E-Ink 라이브러리 (하드웨어 연결 후 활성화)

// ═══════════════════════════════════════
//  설정값 (환경에 맞게 수정)
// ═══════════════════════════════════════

// WiFi 설정
const char* WIFI_SSID     = "YOUR_WIFI_SSID";      // TODO: 실제 WiFi SSID
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // TODO: 실제 WiFi 비밀번호

// MQTT 설정 (라즈베리 파이 IP)
const char* MQTT_BROKER   = "192.168.0.200";        // TODO: 라즈베리 파이 IP
const int   MQTT_PORT     = 1883;
const char* MQTT_CLIENT   = "esp32_esl_001";

// ESL 장치 식별
const char* ESL_MAC       = "AA:BB:CC:DD:EE:01";   // TODO: 실제 MAC 주소

// MQTT 토픽
char TOPIC_UPDATE[64];    // mart/esl/update/<MAC>
char TOPIC_STATUS[64];    // mart/esl/status/<MAC>

// ═══════════════════════════════════════
//  전역 객체
// ═══════════════════════════════════════

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// 현재 표시 중인 정보
String currentProductName = "";
int currentRegularPrice = 0;
int currentSalePrice = 0;
bool displayNeedsUpdate = false;

// ═══════════════════════════════════════
//  WiFi 연결
// ═══════════════════════════════════════

void setupWiFi() {
    Serial.print("[WiFi] Connecting to ");
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WiFi] Connected!");
        Serial.print("[WiFi] IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n[WiFi] Connection FAILED! Restarting...");
        delay(3000);
        ESP.restart();
    }
}

// ═══════════════════════════════════════
//  MQTT 콜백 - 메시지 수신
// ═══════════════════════════════════════

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    Serial.printf("[MQTT] Message on topic: %s\n", topic);

    // JSON 파싱
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload, length);

    if (error) {
        Serial.printf("[MQTT] JSON parse error: %s\n", error.c_str());
        return;
    }

    // ESL 업데이트 데이터 추출
    const char* productName = doc["product_name"] | "Unknown";
    int regularPrice = doc["regular_price"] | 0;
    int salePrice = doc["sale_price"] | 0;
    const char* storeName = doc["store_name"] | "";

    Serial.printf("[ESL] Update: %s | 정가: %d원", productName, regularPrice);
    if (salePrice > 0) {
        Serial.printf(" | 할인가: %d원", salePrice);
    }
    Serial.println();

    // 표시 정보 업데이트
    currentProductName = String(productName);
    currentRegularPrice = regularPrice;
    currentSalePrice = salePrice;
    displayNeedsUpdate = true;

    // 상태 보고
    StaticJsonDocument<256> statusDoc;
    statusDoc["mac_address"] = ESL_MAC;
    statusDoc["status"] = "updated";
    statusDoc["product_name"] = productName;
    statusDoc["regular_price"] = regularPrice;
    statusDoc["sale_price"] = salePrice;
    statusDoc["rssi"] = WiFi.RSSI();

    char statusBuffer[256];
    serializeJson(statusDoc, statusBuffer);
    mqttClient.publish(TOPIC_STATUS, statusBuffer);
    Serial.printf("[MQTT] Status reported to %s\n", TOPIC_STATUS);
}

// ═══════════════════════════════════════
//  MQTT 연결
// ═══════════════════════════════════════

void connectMQTT() {
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);

    while (!mqttClient.connected()) {
        Serial.printf("[MQTT] Connecting to %s:%d...\n", MQTT_BROKER, MQTT_PORT);

        if (mqttClient.connect(MQTT_CLIENT)) {
            Serial.println("[MQTT] Connected!");

            // ESL 업데이트 토픽 구독
            mqttClient.subscribe(TOPIC_UPDATE);
            Serial.printf("[MQTT] Subscribed to %s\n", TOPIC_UPDATE);
        } else {
            Serial.printf("[MQTT] Failed (rc=%d). Retrying in 5s...\n",
                          mqttClient.state());
            delay(5000);
        }
    }
}

// ═══════════════════════════════════════
//  E-Ink 디스플레이 (Step Z에서 완성)
// ═══════════════════════════════════════

void setupDisplay() {
    // TODO (Step Z - 하드웨어 연동):
    // GxEPD2 초기화
    // - SPI 핀 설정 (CS, DC, RST, BUSY)
    // - 디스플레이 해상도 설정
    // - 초기 화면 그리기
    Serial.println("[Display] E-Ink display init (placeholder)");
}

void updateDisplay() {
    if (!displayNeedsUpdate) return;

    Serial.println("[Display] ── E-Ink 화면 업데이트 ──");
    Serial.printf("[Display] 상품명: %s\n", currentProductName.c_str());
    Serial.printf("[Display] 정  가: %d원\n", currentRegularPrice);
    if (currentSalePrice > 0) {
        Serial.printf("[Display] 할인가: %d원\n", currentSalePrice);
        int discount = 100 - (currentSalePrice * 100 / currentRegularPrice);
        Serial.printf("[Display] 할인율: %d%%\n", discount);
    }
    Serial.println("[Display] ─────────────────────");

    // TODO (Step Z - 하드웨어 연동):
    // display.setRotation(1);
    // display.setFullWindow();
    // display.firstPage();
    // do {
    //     display.fillScreen(GxEPD_WHITE);
    //     display.setTextColor(GxEPD_BLACK);
    //     // 상품명 렌더링
    //     // 가격 렌더링
    //     // 할인율 렌더링 (있는 경우)
    //     // 바코드/QR 렌더링 (선택)
    // } while (display.nextPage());

    displayNeedsUpdate = false;
}

// ═══════════════════════════════════════
//  Arduino Setup & Loop
// ═══════════════════════════════════════

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("========================================");
    Serial.println(" Market Path Finder - ESP32 ESL Controller");
    Serial.println("========================================");
    Serial.printf(" MAC: %s\n", ESL_MAC);
    Serial.println("========================================\n");

    // MQTT 토픽 생성 (MAC 주소 포함)
    snprintf(TOPIC_UPDATE, sizeof(TOPIC_UPDATE), "mart/esl/update/%s", ESL_MAC);
    snprintf(TOPIC_STATUS, sizeof(TOPIC_STATUS), "mart/esl/status/%s", ESL_MAC);

    // 1) WiFi 연결
    setupWiFi();

    // 2) E-Ink 디스플레이 초기화
    setupDisplay();

    // 3) MQTT 연결
    connectMQTT();

    Serial.println("\n[System] Ready! Waiting for ESL updates...\n");
}

void loop() {
    // WiFi 재연결 체크
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Disconnected! Reconnecting...");
        setupWiFi();
    }

    // MQTT 재연결 체크
    if (!mqttClient.connected()) {
        connectMQTT();
    }

    // MQTT 메시지 처리
    mqttClient.loop();

    // E-Ink 화면 갱신 (새 메시지 수신 시에만)
    updateDisplay();

    delay(100);
}
