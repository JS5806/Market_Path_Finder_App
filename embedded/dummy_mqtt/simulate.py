#!/usr/bin/env python3
"""
더미 MQTT 시뮬레이터
- 실제 하드웨어(ESP32, iBeacon, NFC) 없이 IoT 메시지를 시뮬레이션
- 개발/테스트 용도로 사용

사용법:
  pip install paho-mqtt
  python simulate.py [--broker localhost] [--port 1883]

시뮬레이션 내용:
  1) Beacon 신호 발행 (3초마다)
  2) NFC 태깅 이벤트 발행 (10초마다)
  3) ESL 업데이트 구독 및 응답
"""
import json
import time
import random
import argparse
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dummy_mqtt")

# ── 매장 시드 데이터 (seed_data.sql 기준) ──
STORE_ID = "550e8400-e29b-41d4-a716-446655440001"

# 더미 비콘 데이터 (매장 내 3개 위치)
DUMMY_BEACONS = [
    {"uuid": "550e8400-e29b-41d4-a716-446655440b01", "major": 1, "minor": 1,
     "x": 2.0, "y": 3.0, "label": "입구 비콘"},
    {"uuid": "550e8400-e29b-41d4-a716-446655440b01", "major": 1, "minor": 2,
     "x": 8.0, "y": 5.0, "label": "중앙 비콘"},
    {"uuid": "550e8400-e29b-41d4-a716-446655440b01", "major": 1, "minor": 3,
     "x": 14.0, "y": 8.0, "label": "계산대 비콘"},
]

# 더미 NFC 태그 UID 목록
DUMMY_NFC_TAGS = [
    "NFC001",
    "NFC002",
    "NFC003",
]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("✅ MQTT 브로커 연결 성공!")
        # ESL 업데이트 토픽 구독 (서버가 보내는 명령 수신)
        client.subscribe("mart/esl/update/#")
        client.subscribe("mart/beacon/config/#")
        client.subscribe("mart/nfc/response/#")
        logger.info("📡 ESL/Beacon/NFC 응답 토픽 구독 완료")
    else:
        logger.error(f"❌ MQTT 연결 실패 (rc={rc})")


def on_message(client, userdata, msg):
    """서버에서 보낸 메시지 수신 (ESL 업데이트 명령 등)"""
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        logger.info(f"📥 수신 [{msg.topic}]: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        # ESL 업데이트 명령 수신 시 → 상태 응답
        if msg.topic.startswith("mart/esl/update/"):
            mac = payload.get("mac_address", "unknown")
            status_topic = f"mart/esl/status/{mac}"
            status_payload = {
                "mac_address": mac,
                "status": "updated",
                "battery": random.randint(60, 100),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            client.publish(status_topic, json.dumps(status_payload))
            logger.info(f"📤 ESL 상태 응답 → {status_topic}")

    except Exception as e:
        logger.error(f"메시지 처리 오류: {e}")


def publish_beacon_signal(client):
    """비콘 신호 시뮬레이션 (모바일 앱이 수신하는 것과 유사)"""
    beacon = random.choice(DUMMY_BEACONS)
    rssi = random.randint(-85, -40)  # RSSI 시뮬레이션

    payload = {
        "beacon_uuid": beacon["uuid"],
        "major": beacon["major"],
        "minor": beacon["minor"],
        "rssi": rssi,
        "store_id": STORE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    topic = f"mart/beacon/signal/{beacon['major']}/{beacon['minor']}"
    client.publish(topic, json.dumps(payload))
    logger.info(
        f"📡 비콘 신호 발행 → {beacon['label']} "
        f"(minor={beacon['minor']}, RSSI={rssi}dBm)"
    )


def publish_nfc_event(client):
    """NFC 태깅 이벤트 시뮬레이션"""
    tag_uid = random.choice(DUMMY_NFC_TAGS)

    payload = {
        "tag_uid": tag_uid,
        "store_id": STORE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    topic = f"mart/nfc/tag/{tag_uid}"
    client.publish(topic, json.dumps(payload))
    logger.info(f"📱 NFC 태깅 시뮬레이션 → tag_uid={tag_uid}")


def main():
    parser = argparse.ArgumentParser(description="더미 MQTT IoT 시뮬레이터")
    parser.add_argument("--broker", default="localhost", help="MQTT 브로커 주소 (기본: localhost)")
    parser.add_argument("--port", type=int, default=1883, help="MQTT 브로커 포트 (기본: 1883)")
    args = parser.parse_args()

    logger.info(f"🚀 더미 MQTT 시뮬레이터 시작 (broker={args.broker}:{args.port})")
    logger.info("   - 비콘 신호: 3초마다 발행")
    logger.info("   - NFC 태깅: 10초마다 발행")
    logger.info("   - ESL 명령: 서버 발행 시 자동 응답")
    logger.info("")

    client = mqtt.Client(client_id="dummy_iot_simulator", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(args.broker, args.port, keepalive=60)
        client.loop_start()
    except ConnectionRefusedError:
        logger.error(f"❌ MQTT 브로커에 연결할 수 없습니다 ({args.broker}:{args.port})")
        logger.error("   → Docker에서 Mosquitto가 실행 중인지 확인하세요:")
        logger.error("   → docker ps | grep mosquitto")
        return

    beacon_interval = 3   # 초
    nfc_interval = 10     # 초
    last_beacon = 0
    last_nfc = 0

    try:
        while True:
            now = time.time()

            if now - last_beacon >= beacon_interval:
                publish_beacon_signal(client)
                last_beacon = now

            if now - last_nfc >= nfc_interval:
                publish_nfc_event(client)
                last_nfc = now

            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("\n🛑 시뮬레이터 종료 중...")
        client.loop_stop()
        client.disconnect()
        logger.info("✅ 정상 종료")


if __name__ == "__main__":
    main()
