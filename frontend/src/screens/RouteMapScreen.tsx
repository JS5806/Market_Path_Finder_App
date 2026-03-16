/**
 * 경로 지도 화면 - 매장 내 최적 경로 시각화 (SVG)
 * SafeArea 적용 + 비콘 기반 실시간 위치 표시 + 현재 위치에서 재탐색 버튼
 */
import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Line, Text as SvgText, Rect } from 'react-native-svg';
import { routeAPI, iotAPI } from '../services/api';
import { DEFAULT_STORE_ID } from '../store/storeConfig';

const SCREEN_WIDTH = Dimensions.get('window').width;
const MAP_PADDING = 20;
const MAP_WIDTH = SCREEN_WIDTH - MAP_PADDING * 2;
const MAP_HEIGHT = MAP_WIDTH * 0.8;
const SCALE_X = (MAP_WIDTH - 40) / 40; // 매장 가로 40m
const SCALE_Y = (MAP_HEIGHT - 40) / 30; // 매장 세로 30m

const toX = (x: number) => x * SCALE_X + 20;
const toY = (y: number) => y * SCALE_Y + 20;

// 가장 가까운 노드 찾기 (비콘 좌표 → 노드 매핑)
const findNearestNode = (x: number, y: number, nodes: any[]) => {
  let minDist = Infinity;
  let nearest = null;
  for (const n of nodes) {
    const dist = Math.sqrt((n.x - x) ** 2 + (n.y - y) ** 2);
    if (dist < minDist) {
      minDist = dist;
      nearest = n;
    }
  }
  return nearest;
};

export default function RouteMapScreen({ route: navRoute }: any) {
  const insets = useSafeAreaInsets();
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [routeData, setRouteData] = useState<any>(navRoute?.params?.routeData || null);
  const [loading, setLoading] = useState(true);
  const [rerouteLoading, setRerouteLoading] = useState(false);

  // 실시간 사용자 위치 (비콘 기반 추정 좌표)
  const [userPosition, setUserPosition] = useState<{ x: number; y: number } | null>(null);
  const beaconIntervalRef = useRef<any>(null);

  useEffect(() => {
    loadMapData();
    startBeaconTracking();
    return () => {
      if (beaconIntervalRef.current) {
        clearInterval(beaconIntervalRef.current);
      }
    };
  }, []);

  const loadMapData = async () => {
    try {
      const [nodesRes, edgesRes] = await Promise.all([
        routeAPI.getNodes(DEFAULT_STORE_ID),
        routeAPI.getEdges(DEFAULT_STORE_ID),
      ]);
      setNodes(nodesRes.data.data || []);
      setEdges(edgesRes.data.data || []);
    } catch {
      Alert.alert('오류', '매장 지도 데이터를 불러오지 못했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 비콘 기반 위치 추적 (주기적으로 서버에 위치 요청)
  const startBeaconTracking = () => {
    // 최초 1회 위치 가져오기
    fetchBeaconPosition();
    // 5초 간격으로 위치 업데이트
    beaconIntervalRef.current = setInterval(() => {
      fetchBeaconPosition();
    }, 5000);
  };

  const fetchBeaconPosition = async () => {
    try {
      // 비콘 시그널을 서버에 보내서 위치 추정 받기
      // 실제로는 BLE 스캔 결과를 보내지만, 여기서는 서버의 마지막 위치 추정값 사용
      const res = await iotAPI.getBeacons(DEFAULT_STORE_ID);
      const beacons = res.data.data || res.data || [];

      // 비콘 데이터에 estimated_position이 있으면 사용
      // 없으면 비콘 위치들의 가중 평균으로 추정
      if (beacons.length > 0) {
        // 가장 최근 시그널이 강한 비콘 기준으로 위치 추정
        const sorted = [...beacons].sort((a: any, b: any) => (b.rssi || -100) - (a.rssi || -100));
        const strongest = sorted[0];
        if (strongest.x !== undefined && strongest.y !== undefined) {
          setUserPosition({ x: strongest.x, y: strongest.y });
        }
      }
    } catch {
      // 비콘 데이터 없으면 무시 (위치 표시 안함)
    }
  };

  // 현재 위치에서 재탐색
  const handleRerouteFromCurrent = async () => {
    if (!userPosition || nodes.length === 0) {
      Alert.alert('알림', '현재 위치를 확인할 수 없습니다. 비콘 신호를 확인해주세요.');
      return;
    }

    setRerouteLoading(true);
    try {
      // 현재 위치에서 가장 가까운 노드를 시작점으로 설정
      const nearestNode = findNearestNode(userPosition.x, userPosition.y, nodes);
      if (!nearestNode) {
        Alert.alert('오류', '가까운 노드를 찾을 수 없습니다');
        return;
      }

      const res = await routeAPI.optimizeFromCart({
        store_id: DEFAULT_STORE_ID,
        start_node_id: nearestNode.node_id,
      });
      const newRoute = res.data.data || res.data;
      setRouteData(newRoute);
      Alert.alert('경로 재탐색 완료', `현재 위치(${nearestNode.label || '노드 ' + nearestNode.node_id})에서 새 경로를 계산했습니다.`);
    } catch (e: any) {
      const msg = e.response?.data?.detail || '경로 재탐색에 실패했습니다';
      Alert.alert('오류', msg);
    } finally {
      setRerouteLoading(false);
    }
  };

  const getNodeColor = (nodeType: string) => {
    switch (nodeType) {
      case 'entrance': return '#00b894';
      case 'checkout': return '#d63031';
      case 'shelf': return '#0984e3';
      default: return '#b2bec3';
    }
  };

  const isRouteNode = (nodeId: number) => {
    if (!routeData) return false;
    return routeData.visit_order?.some((s: any) => s.node_id === nodeId);
  };

  const getRouteOrder = (nodeId: number) => {
    if (!routeData) return -1;
    const stop = routeData.visit_order?.find((s: any) => s.node_id === nodeId);
    return stop ? stop.order : -1;
  };

  const routeSegments = routeData?.segments || [];

  if (loading) {
    return (
      <View style={[styles.center, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 12, color: '#636e72' }}>매장 지도 로딩 중...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={[styles.container, { paddingTop: insets.top }]}>
      <Text style={styles.title}>매장 지도</Text>

      {/* SVG 매장 지도 */}
      <View style={styles.mapContainer}>
        <Svg width={MAP_WIDTH} height={MAP_HEIGHT}>
          {/* 배경 */}
          <Rect x={0} y={0} width={MAP_WIDTH} height={MAP_HEIGHT}
            fill="#f1f2f6" rx={12} />

          {/* 간선 (통로) */}
          {edges.map((e: any) => {
            const from = nodes.find((n: any) => n.node_id === e.from_node_id);
            const to = nodes.find((n: any) => n.node_id === e.to_node_id);
            if (!from || !to) return null;
            return (
              <Line
                key={e.edge_id}
                x1={toX(from.x)} y1={toY(from.y)}
                x2={toX(to.x)} y2={toY(to.y)}
                stroke="#dfe6e9" strokeWidth={2}
              />
            );
          })}

          {/* 경로 하이라이트 */}
          {routeSegments.map((seg: any, idx: number) => {
            const pathIds = seg.path_node_ids || [];
            const lines = [];
            for (let i = 0; i < pathIds.length - 1; i++) {
              const from = nodes.find((n: any) => n.node_id === pathIds[i]);
              const to = nodes.find((n: any) => n.node_id === pathIds[i + 1]);
              if (from && to) {
                lines.push(
                  <Line
                    key={`route-${idx}-${i}`}
                    x1={toX(from.x)} y1={toY(from.y)}
                    x2={toX(to.x)} y2={toY(to.y)}
                    stroke="#e17055" strokeWidth={4} strokeLinecap="round"
                  />
                );
              }
            }
            return lines;
          })}

          {/* 노드 */}
          {nodes.map((n: any) => {
            const isOnRoute = isRouteNode(n.node_id);
            const order = getRouteOrder(n.node_id);
            const radius = isOnRoute ? 12 : 6;
            return (
              <React.Fragment key={n.node_id}>
                <Circle
                  cx={toX(n.x)} cy={toY(n.y)} r={radius}
                  fill={isOnRoute ? '#e17055' : getNodeColor(n.node_type)}
                  stroke={isOnRoute ? '#d63031' : '#fff'}
                  strokeWidth={isOnRoute ? 3 : 1}
                />
                {isOnRoute && order >= 0 && (
                  <SvgText
                    x={toX(n.x)} y={toY(n.y) + 4}
                    textAnchor="middle" fill="#fff"
                    fontSize={10} fontWeight="bold"
                  >
                    {order + 1}
                  </SvgText>
                )}
                {n.label && (
                  <SvgText
                    x={toX(n.x)} y={toY(n.y) - radius - 4}
                    textAnchor="middle" fill="#2d3436"
                    fontSize={8}
                  >
                    {n.label}
                  </SvgText>
                )}
              </React.Fragment>
            );
          })}

          {/* 실시간 사용자 위치 (비콘 기반) */}
          {userPosition && (
            <>
              {/* 외곽 펄스 원 */}
              <Circle
                cx={toX(userPosition.x)} cy={toY(userPosition.y)} r={18}
                fill="rgba(116, 185, 255, 0.2)"
                stroke="rgba(116, 185, 255, 0.5)" strokeWidth={2}
              />
              {/* 내부 점 */}
              <Circle
                cx={toX(userPosition.x)} cy={toY(userPosition.y)} r={8}
                fill="#74b9ff" stroke="#fff" strokeWidth={3}
              />
              <SvgText
                x={toX(userPosition.x)} y={toY(userPosition.y) - 22}
                textAnchor="middle" fill="#0984e3"
                fontSize={9} fontWeight="bold"
              >
                내 위치
              </SvgText>
            </>
          )}
        </Svg>
      </View>

      {/* 범례 */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#00b894' }]} />
          <Text style={styles.legendText}>입구</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#0984e3' }]} />
          <Text style={styles.legendText}>진열대</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#d63031' }]} />
          <Text style={styles.legendText}>계산대</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#e17055' }]} />
          <Text style={styles.legendText}>경로</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#74b9ff' }]} />
          <Text style={styles.legendText}>내 위치</Text>
        </View>
      </View>

      {/* 현재 위치에서 재탐색 버튼 */}
      <View style={styles.actionRow}>
        <TouchableOpacity
          style={[styles.rerouteButton, rerouteLoading && styles.buttonDisabled]}
          onPress={handleRerouteFromCurrent}
          disabled={rerouteLoading}
        >
          {rerouteLoading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.rerouteButtonText}>📍 현재 위치에서 재탐색</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* 경로 정보 */}
      {routeData && (
        <View style={styles.routeInfo}>
          <Text style={styles.routeTitle}>최적 경로 안내</Text>
          <Text style={styles.routeSummary}>
            총 거리: {routeData.total_distance}m | 예상 시간: {routeData.estimated_time_min}분
          </Text>
          {routeData.visit_order?.map((stop: any) => (
            <View key={stop.order} style={styles.stopItem}>
              <View style={styles.stopNumber}>
                <Text style={styles.stopNumberText}>{stop.order + 1}</Text>
              </View>
              <View style={styles.stopInfo}>
                <Text style={styles.stopLabel}>{stop.label || '통과 지점'}</Text>
                {stop.product_names?.length > 0 && (
                  <Text style={styles.stopProducts}>
                    📦 {stop.product_names.join(', ')}
                  </Text>
                )}
              </View>
            </View>
          ))}
        </View>
      )}

      {/* 하단 여백 */}
      <View style={{ height: 20 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: {
    fontSize: 20, fontWeight: 'bold', color: '#2d3436',
    paddingHorizontal: 20, paddingVertical: 14,
  },
  mapContainer: {
    alignItems: 'center', marginHorizontal: MAP_PADDING,
    backgroundColor: '#fff', borderRadius: 16, padding: 8,
    shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 8, elevation: 3,
  },
  legend: {
    flexDirection: 'row', justifyContent: 'center', gap: 12,
    paddingVertical: 12, flexWrap: 'wrap',
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { fontSize: 11, color: '#636e72' },

  // 재탐색 버튼
  actionRow: {
    paddingHorizontal: 20, paddingVertical: 8,
  },
  rerouteButton: {
    backgroundColor: '#0984e3', borderRadius: 12,
    paddingVertical: 14, alignItems: 'center',
  },
  rerouteButtonText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
  buttonDisabled: { opacity: 0.6 },

  routeInfo: {
    margin: 16, backgroundColor: '#fff', borderRadius: 12, padding: 16,
  },
  routeTitle: { fontSize: 16, fontWeight: 'bold', color: '#2d3436', marginBottom: 8 },
  routeSummary: { fontSize: 13, color: '#636e72', marginBottom: 12 },
  stopItem: {
    flexDirection: 'row', alignItems: 'flex-start', marginBottom: 10,
  },
  stopNumber: {
    width: 28, height: 28, borderRadius: 14, backgroundColor: '#e17055',
    justifyContent: 'center', alignItems: 'center', marginRight: 10,
  },
  stopNumberText: { color: '#fff', fontWeight: 'bold', fontSize: 13 },
  stopInfo: { flex: 1 },
  stopLabel: { fontSize: 14, fontWeight: '600', color: '#2d3436' },
  stopProducts: { fontSize: 12, color: '#0984e3', marginTop: 2 },
});
