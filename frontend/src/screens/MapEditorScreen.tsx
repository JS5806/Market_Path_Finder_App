/**
 * 매장 지도 에디터 (관리자 전용)
 * 기능:
 * 1. 평면도 이미지 업로드 (PNG/JPG/SVG/PDF/DWG/DXF)
 * 2. 평면도 위에 노드 추가 (터치) - 타입: 입구/계산대/진열대(섹션)/통로(경로)
 * 3. 두 노드 선택 → 엣지(경로) 연결
 * 4. 노드 삭제 / 엣지 삭제
 *
 * 노드 타입 설계:
 * - entrance: 입구
 * - checkout: 계산대
 * - shelf: 상품 섹션 (음료, 과자, 냉동식품 등)
 * - waypoint: 통로/경로 노드 (벽을 뚫지 않도록 경로 중간점)
 *
 * 경로 예시: 음료섹션(shelf) → 경로1(waypoint) → 과자섹션(shelf) → 경로2(waypoint) → 계산대(checkout)
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Alert, ActivityIndicator, Modal, TextInput,
  PanResponder, Image,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Line, Text as SvgText, Rect, Image as SvgImage, G, Defs, Pattern, Path } from 'react-native-svg';
import { routeAPI } from '../services/api';
import { DEFAULT_STORE_ID } from '../store/storeConfig';

// 샘플 평면도 (SVG 기반 내장 템플릿)
const SAMPLE_FLOORPLANS = [
  {
    id: 'supermarket_basic',
    name: '기본 슈퍼마켓',
    desc: '40m x 30m, 4개 통로',
    thumbnail: '🏪',
    // 미리 정의된 벽/구역 데이터
    walls: [
      // 외벽
      { x1: 0, y1: 0, x2: 40, y2: 0 },
      { x1: 40, y1: 0, x2: 40, y2: 30 },
      { x1: 40, y1: 30, x2: 0, y2: 30 },
      { x1: 0, y1: 30, x2: 0, y2: 0 },
      // 진열대 간 벽(선반)
      { x1: 8, y1: 5, x2: 8, y2: 25 },
      { x1: 16, y1: 5, x2: 16, y2: 25 },
      { x1: 24, y1: 5, x2: 24, y2: 25 },
      { x1: 32, y1: 5, x2: 32, y2: 25 },
    ],
    zones: [
      { x: 4, y: 15, w: 6, h: 18, label: '신선식품', color: '#00b894' },
      { x: 12, y: 15, w: 6, h: 18, label: '음료/주류', color: '#0984e3' },
      { x: 20, y: 15, w: 6, h: 18, label: '과자/스낵', color: '#e17055' },
      { x: 28, y: 15, w: 6, h: 18, label: '냉동식품', color: '#6c5ce7' },
      { x: 36, y: 3, w: 3, h: 5, label: '계산대', color: '#d63031' },
    ],
  },
  {
    id: 'mart_large',
    name: '대형마트 (L자형)',
    desc: '40m x 30m, L자 구조',
    thumbnail: '🏬',
    walls: [
      { x1: 0, y1: 0, x2: 40, y2: 0 },
      { x1: 40, y1: 0, x2: 40, y2: 20 },
      { x1: 40, y1: 20, x2: 25, y2: 20 },
      { x1: 25, y1: 20, x2: 25, y2: 30 },
      { x1: 25, y1: 30, x2: 0, y2: 30 },
      { x1: 0, y1: 30, x2: 0, y2: 0 },
      // 내부 선반
      { x1: 6, y1: 4, x2: 6, y2: 16 },
      { x1: 12, y1: 4, x2: 12, y2: 16 },
      { x1: 18, y1: 4, x2: 18, y2: 16 },
      { x1: 6, y1: 22, x2: 6, y2: 28 },
      { x1: 12, y1: 22, x2: 12, y2: 28 },
    ],
    zones: [
      { x: 3, y: 10, w: 4, h: 10, label: '식품', color: '#00b894' },
      { x: 9, y: 10, w: 4, h: 10, label: '음료', color: '#0984e3' },
      { x: 15, y: 10, w: 4, h: 10, label: '생활용품', color: '#fdcb6e' },
      { x: 30, y: 10, w: 8, h: 8, label: '가전', color: '#e17055' },
      { x: 3, y: 25, w: 4, h: 4, label: '냉동', color: '#6c5ce7' },
      { x: 9, y: 25, w: 4, h: 4, label: '유제품', color: '#a29bfe' },
      { x: 38, y: 2, w: 2, h: 4, label: '계산대', color: '#d63031' },
    ],
  },
  {
    id: 'convenience',
    name: '편의점',
    desc: '15m x 10m, 소형 매장',
    thumbnail: '🏪',
    walls: [
      { x1: 0, y1: 0, x2: 40, y2: 0 },
      { x1: 40, y1: 0, x2: 40, y2: 30 },
      { x1: 40, y1: 30, x2: 0, y2: 30 },
      { x1: 0, y1: 30, x2: 0, y2: 0 },
      // 진열대
      { x1: 8, y1: 6, x2: 8, y2: 24 },
      { x1: 18, y1: 6, x2: 18, y2: 24 },
      { x1: 28, y1: 6, x2: 28, y2: 24 },
    ],
    zones: [
      { x: 4, y: 15, w: 6, h: 16, label: '음료/냉장', color: '#0984e3' },
      { x: 13, y: 15, w: 8, h: 16, label: '과자/식품', color: '#e17055' },
      { x: 23, y: 15, w: 8, h: 16, label: '생활/잡화', color: '#fdcb6e' },
      { x: 35, y: 3, w: 4, h: 5, label: '카운터', color: '#d63031' },
    ],
  },
];

const SCREEN_WIDTH = Dimensions.get('window').width;
const MAP_PADDING = 10;
const MAP_WIDTH = SCREEN_WIDTH - MAP_PADDING * 2;
const MAP_HEIGHT = MAP_WIDTH * 0.85;
// 매장 실제 크기 (m) - 추후 서버에서 받아올 수 있음
const STORE_W = 40;
const STORE_H = 30;
const SCALE_X = (MAP_WIDTH - 20) / STORE_W;
const SCALE_Y = (MAP_HEIGHT - 20) / STORE_H;

const toSvgX = (mx: number) => mx * SCALE_X + 10;
const toSvgY = (my: number) => my * SCALE_Y + 10;
const toMapX = (sx: number) => Math.max(0, Math.min(STORE_W, (sx - 10) / SCALE_X));
const toMapY = (sy: number) => Math.max(0, Math.min(STORE_H, (sy - 10) / SCALE_Y));

type EditorMode = 'select' | 'addNode' | 'addEdge' | 'delete';

interface NodeData {
  node_id: number;
  x: number;
  y: number;
  node_type: string;
  label: string | null;
  floor: number;
}

interface EdgeData {
  edge_id: number;
  from_node_id: number;
  to_node_id: number;
  distance: number;
  is_bidirectional: boolean;
}

const NODE_TYPES = [
  { value: 'entrance', label: '입구', color: '#00b894', icon: '🚪' },
  { value: 'checkout', label: '계산대', color: '#d63031', icon: '💳' },
  { value: 'shelf', label: '진열대(섹션)', color: '#0984e3', icon: '📦' },
  { value: 'waypoint', label: '통로(경로)', color: '#fdcb6e', icon: '🔶' },
];

const getNodeColor = (type: string) =>
  NODE_TYPES.find(t => t.value === type)?.color || '#b2bec3';

export default function MapEditorScreen() {
  const insets = useSafeAreaInsets();
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<EditorMode>('select');
  const [selectedNodeType, setSelectedNodeType] = useState('waypoint');
  const [selectedNodes, setSelectedNodes] = useState<number[]>([]);
  const [floorplanUrl, setFloorplanUrl] = useState<string | null>(null);
  const [selectedFloorplan, setSelectedFloorplan] = useState<typeof SAMPLE_FLOORPLANS[0] | null>(null);

  // 평면도 업로드 모달
  const [uploadModal, setUploadModal] = useState(false);
  const [imageUrlInput, setImageUrlInput] = useState('');
  const [uploadingImage, setUploadingImage] = useState(false);

  // 노드 라벨 모달
  const [labelModal, setLabelModal] = useState(false);
  const [pendingNode, setPendingNode] = useState<{ x: number; y: number } | null>(null);
  const [nodeLabel, setNodeLabel] = useState('');

  useEffect(() => { loadMapData(); }, []);

  const loadMapData = async () => {
    setLoading(true);
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

  // 맵 터치 → 좌표 → 노드 추가
  const handleMapPress = (evt: any) => {
    if (mode !== 'addNode') return;

    const { locationX, locationY } = evt.nativeEvent;
    const mx = toMapX(locationX);
    const my = toMapY(locationY);

    setPendingNode({ x: Math.round(mx * 10) / 10, y: Math.round(my * 10) / 10 });
    setNodeLabel('');
    setLabelModal(true);
  };

  // 노드 생성 확정
  const confirmAddNode = async () => {
    if (!pendingNode) return;
    setLabelModal(false);
    try {
      const res = await routeAPI.createNode({
        store_id: DEFAULT_STORE_ID,
        x: pendingNode.x,
        y: pendingNode.y,
        node_type: selectedNodeType,
        label: nodeLabel.trim() || undefined,
      });
      const newNode = res.data.data;
      setNodes(prev => [...prev, newNode]);
      setPendingNode(null);
    } catch (e: any) {
      Alert.alert('오류', e.response?.data?.detail || '노드 추가 실패');
    }
  };

  // 노드 클릭
  const handleNodePress = async (nodeId: number) => {
    if (mode === 'delete') {
      const node = nodes.find(n => n.node_id === nodeId);
      Alert.alert('노드 삭제', `"${node?.label || '노드 ' + nodeId}"를 삭제할까요?\n연결된 엣지도 함께 삭제됩니다.`, [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제', style: 'destructive', onPress: async () => {
            try {
              await routeAPI.deleteNode(nodeId);
              setNodes(prev => prev.filter(n => n.node_id !== nodeId));
              setEdges(prev => prev.filter(e => e.from_node_id !== nodeId && e.to_node_id !== nodeId));
            } catch {
              Alert.alert('오류', '삭제 실패');
            }
          },
        },
      ]);
      return;
    }

    if (mode === 'addEdge') {
      setSelectedNodes(prev => {
        const updated = [...prev, nodeId];
        if (updated.length === 2) {
          // 두 노드 선택 완료 → 엣지 생성
          createEdgeBetween(updated[0], updated[1]);
          return [];
        }
        return updated;
      });
      return;
    }

    // select 모드: 노드 정보 표시
    const node = nodes.find(n => n.node_id === nodeId);
    if (node) {
      const typeInfo = NODE_TYPES.find(t => t.value === node.node_type);
      Alert.alert(
        `${typeInfo?.icon || ''} ${node.label || '노드 ' + node.node_id}`,
        `타입: ${typeInfo?.label || node.node_type}\n좌표: (${node.x}, ${node.y})`,
      );
    }
  };

  // 엣지 생성
  const createEdgeBetween = async (from: number, to: number) => {
    if (from === to) {
      Alert.alert('알림', '같은 노드를 연결할 수 없습니다');
      return;
    }
    // 이미 연결되어 있는지 확인
    const exists = edges.some(
      e => (e.from_node_id === from && e.to_node_id === to) ||
           (e.from_node_id === to && e.to_node_id === from)
    );
    if (exists) {
      Alert.alert('알림', '이미 연결된 노드입니다');
      return;
    }

    try {
      const res = await routeAPI.createEdge({
        store_id: DEFAULT_STORE_ID,
        from_node_id: from,
        to_node_id: to,
      });
      const newEdge = res.data.data;
      setEdges(prev => [...prev, newEdge]);
    } catch (e: any) {
      Alert.alert('오류', e.response?.data?.detail || '엣지 생성 실패');
    }
  };

  // 엣지 삭제
  const handleEdgePress = (edgeId: number) => {
    if (mode !== 'delete') return;
    const edge = edges.find(e => e.edge_id === edgeId);
    if (!edge) return;

    const from = nodes.find(n => n.node_id === edge.from_node_id);
    const to = nodes.find(n => n.node_id === edge.to_node_id);

    Alert.alert('엣지 삭제', `"${from?.label || edge.from_node_id}" ↔ "${to?.label || edge.to_node_id}" 연결을 삭제할까요?`, [
      { text: '취소', style: 'cancel' },
      {
        text: '삭제', style: 'destructive', onPress: async () => {
          try {
            await routeAPI.deleteEdge(edgeId);
            setEdges(prev => prev.filter(e => e.edge_id !== edgeId));
          } catch {
            Alert.alert('오류', '삭제 실패');
          }
        },
      },
    ]);
  };

  // 평면도 업로드 모달 열기
  const handleUploadFloorplan = () => {
    setUploadModal(true);
  };

  // 샘플 평면도 선택
  const selectSampleFloorplan = (sample: typeof SAMPLE_FLOORPLANS[0]) => {
    setSelectedFloorplan(sample);
    setFloorplanUrl(null);
    setUploadModal(false);
    Alert.alert('평면도 적용', `"${sample.name}" 평면도가 적용되었습니다.\n이제 노드와 경로를 편집할 수 있습니다.`);
  };

  // URL로 이미지 업로드
  const handleUrlUpload = async () => {
    const url = imageUrlInput.trim();
    if (!url) {
      Alert.alert('알림', '이미지 URL을 입력해주세요');
      return;
    }
    // 기본 URL 검증
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      Alert.alert('알림', 'http:// 또는 https://로 시작하는 URL을 입력해주세요');
      return;
    }

    setUploadingImage(true);
    try {
      // 이미지 로드 가능 여부 확인
      await new Promise<void>((resolve, reject) => {
        Image.getSize(
          url,
          (width, height) => {
            console.log(`이미지 로드 성공: ${width}x${height}`);
            resolve();
          },
          (error) => {
            reject(new Error('이미지를 불러올 수 없습니다'));
          },
        );
      });

      setFloorplanUrl(url);
      setSelectedFloorplan(null);
      setImageUrlInput('');
      setUploadModal(false);
      Alert.alert('업로드 성공', '평면도 이미지가 적용되었습니다.\n이제 노드와 경로를 편집할 수 있습니다.');
    } catch (e: any) {
      Alert.alert('오류', e.message || '이미지를 불러올 수 없습니다. URL을 확인해주세요.');
    } finally {
      setUploadingImage(false);
    }
  };

  // 평면도 제거
  const clearFloorplan = () => {
    Alert.alert('평면도 제거', '현재 평면도를 제거하시겠습니까?\n노드와 엣지는 유지됩니다.', [
      { text: '취소', style: 'cancel' },
      {
        text: '제거', style: 'destructive', onPress: () => {
          setSelectedFloorplan(null);
          setFloorplanUrl(null);
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={[styles.center, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>지도 데이터 로딩 중...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* 헤더 */}
      <View style={styles.header}>
        <Text style={styles.title}>매장 지도 편집기</Text>
        <View style={{ flexDirection: 'row', gap: 6 }}>
          {(selectedFloorplan || floorplanUrl) && (
            <TouchableOpacity style={[styles.uploadBtn, { backgroundColor: 'rgba(255,100,100,0.3)' }]} onPress={clearFloorplan}>
              <Text style={styles.uploadBtnText}>✕ 제거</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={styles.uploadBtn} onPress={handleUploadFloorplan}>
            <Text style={styles.uploadBtnText}>📐 평면도 {selectedFloorplan || floorplanUrl ? '변경' : '업로드'}</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 현재 적용된 평면도 표시 */}
      {(selectedFloorplan || floorplanUrl) && (
        <View style={styles.floorplanBadge}>
          <Text style={styles.floorplanBadgeText}>
            {selectedFloorplan ? `📐 ${selectedFloorplan.name}` : '🖼️ 외부 이미지 평면도'} 적용 중
          </Text>
        </View>
      )}

      {/* 모드 선택 툴바 */}
      <View style={styles.toolbar}>
        {([
          { mode: 'select' as EditorMode, label: '선택', icon: '👆' },
          { mode: 'addNode' as EditorMode, label: '노드 추가', icon: '📍' },
          { mode: 'addEdge' as EditorMode, label: '경로 연결', icon: '🔗' },
          { mode: 'delete' as EditorMode, label: '삭제', icon: '🗑️' },
        ]).map(item => (
          <TouchableOpacity
            key={item.mode}
            style={[styles.toolBtn, mode === item.mode && styles.toolBtnActive]}
            onPress={() => { setMode(item.mode); setSelectedNodes([]); }}
          >
            <Text style={styles.toolIcon}>{item.icon}</Text>
            <Text style={[styles.toolLabel, mode === item.mode && styles.toolLabelActive]}>
              {item.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 노드 타입 선택 (addNode 모드일 때만) */}
      {mode === 'addNode' && (
        <View style={styles.typeSelector}>
          <Text style={styles.typeSelectorLabel}>노드 타입:</Text>
          {NODE_TYPES.map(t => (
            <TouchableOpacity
              key={t.value}
              style={[styles.typeChip, selectedNodeType === t.value && {
                backgroundColor: t.color, borderColor: t.color,
              }]}
              onPress={() => setSelectedNodeType(t.value)}
            >
              <Text style={[styles.typeChipText, selectedNodeType === t.value && { color: '#fff' }]}>
                {t.icon} {t.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* 안내 메시지 */}
      {mode === 'addEdge' && (
        <View style={styles.hintBar}>
          <Text style={styles.hintText}>
            {selectedNodes.length === 0
              ? '연결할 첫 번째 노드를 터치하세요'
              : '두 번째 노드를 터치하면 경로가 연결됩니다'}
          </Text>
        </View>
      )}
      {mode === 'delete' && (
        <View style={[styles.hintBar, { backgroundColor: '#fff0f0' }]}>
          <Text style={[styles.hintText, { color: '#d63031' }]}>
            삭제할 노드 또는 엣지를 터치하세요
          </Text>
        </View>
      )}

      {/* SVG 맵 에디터 */}
      <ScrollView contentContainerStyle={styles.mapScroll}>
        <View
          style={styles.mapContainer}
          onStartShouldSetResponder={() => mode === 'addNode'}
          onResponderRelease={handleMapPress}
        >
          <Svg width={MAP_WIDTH} height={MAP_HEIGHT}>
            {/* 그리드 배경 */}
            <Rect x={0} y={0} width={MAP_WIDTH} height={MAP_HEIGHT} fill="#fafafa" rx={8} stroke="#dfe6e9" strokeWidth={1} />

            {/* URL 이미지 평면도 */}
            {floorplanUrl && (
              <SvgImage
                href={{ uri: floorplanUrl }}
                x={5} y={5}
                width={MAP_WIDTH - 10} height={MAP_HEIGHT - 10}
                opacity={0.5}
                preserveAspectRatio="xMidYMid meet"
              />
            )}

            {/* 샘플 평면도 벽과 구역 */}
            {selectedFloorplan && (
              <G>
                {/* 구역 배경 */}
                {selectedFloorplan.zones.map((z, i) => (
                  <G key={`zone${i}`}>
                    <Rect
                      x={toSvgX(z.x - z.w / 2)}
                      y={toSvgY(z.y - z.h / 2)}
                      width={z.w * SCALE_X}
                      height={z.h * SCALE_Y}
                      fill={z.color}
                      opacity={0.12}
                      rx={4}
                    />
                    <SvgText
                      x={toSvgX(z.x)} y={toSvgY(z.y)}
                      textAnchor="middle" fill={z.color} fontSize={9} fontWeight="bold"
                      opacity={0.8}
                    >
                      {z.label}
                    </SvgText>
                  </G>
                ))}
                {/* 벽/선반 라인 */}
                {selectedFloorplan.walls.map((w, i) => (
                  <Line
                    key={`wall${i}`}
                    x1={toSvgX(w.x1)} y1={toSvgY(w.y1)}
                    x2={toSvgX(w.x2)} y2={toSvgY(w.y2)}
                    stroke="#636e72" strokeWidth={2} opacity={0.4}
                  />
                ))}
              </G>
            )}

            {/* 5m 간격 그리드 */}
            {Array.from({ length: Math.floor(STORE_W / 5) + 1 }).map((_, i) => (
              <Line key={`gv${i}`}
                x1={toSvgX(i * 5)} y1={toSvgY(0)}
                x2={toSvgX(i * 5)} y2={toSvgY(STORE_H)}
                stroke={selectedFloorplan || floorplanUrl ? 'rgba(0,0,0,0.06)' : '#f1f2f6'} strokeWidth={0.5}
              />
            ))}
            {Array.from({ length: Math.floor(STORE_H / 5) + 1 }).map((_, i) => (
              <Line key={`gh${i}`}
                x1={toSvgX(0)} y1={toSvgY(i * 5)}
                x2={toSvgX(STORE_W)} y2={toSvgY(i * 5)}
                stroke={selectedFloorplan || floorplanUrl ? 'rgba(0,0,0,0.06)' : '#f1f2f6'} strokeWidth={0.5}
              />
            ))}
            {/* 축 라벨 */}
            {Array.from({ length: Math.floor(STORE_W / 10) + 1 }).map((_, i) => (
              <SvgText key={`lx${i}`} x={toSvgX(i * 10)} y={MAP_HEIGHT - 2}
                textAnchor="middle" fill="#b2bec3" fontSize={8}>
                {i * 10}m
              </SvgText>
            ))}

            {/* 엣지 (통로) */}
            {edges.map(e => {
              const from = nodes.find(n => n.node_id === e.from_node_id);
              const to = nodes.find(n => n.node_id === e.to_node_id);
              if (!from || !to) return null;
              return (
                <Line
                  key={`e${e.edge_id}`}
                  x1={toSvgX(from.x)} y1={toSvgY(from.y)}
                  x2={toSvgX(to.x)} y2={toSvgY(to.y)}
                  stroke={mode === 'delete' ? '#e17055' : '#b2bec3'}
                  strokeWidth={mode === 'delete' ? 4 : 2.5}
                  strokeLinecap="round"
                  onPress={() => handleEdgePress(e.edge_id)}
                />
              );
            })}

            {/* 노드 */}
            {nodes.map(n => {
              const isSelected = selectedNodes.includes(n.node_id);
              const r = n.node_type === 'waypoint' ? 7 : 10;
              return (
                <React.Fragment key={`n${n.node_id}`}>
                  {isSelected && (
                    <Circle cx={toSvgX(n.x)} cy={toSvgY(n.y)} r={r + 5}
                      fill="none" stroke="#0984e3" strokeWidth={2} strokeDasharray="4,2" />
                  )}
                  <Circle
                    cx={toSvgX(n.x)} cy={toSvgY(n.y)} r={r}
                    fill={getNodeColor(n.node_type)}
                    stroke="#fff" strokeWidth={2}
                    onPress={() => handleNodePress(n.node_id)}
                  />
                  {n.label && (
                    <SvgText
                      x={toSvgX(n.x)} y={toSvgY(n.y) - r - 4}
                      textAnchor="middle" fill="#2d3436" fontSize={8} fontWeight="bold"
                    >
                      {n.label}
                    </SvgText>
                  )}
                  <SvgText
                    x={toSvgX(n.x)} y={toSvgY(n.y) + 3}
                    textAnchor="middle" fill="#fff" fontSize={7} fontWeight="bold"
                  >
                    {n.node_id}
                  </SvgText>
                </React.Fragment>
              );
            })}

            {/* 임시 추가 노드 미리보기 */}
            {pendingNode && (
              <Circle
                cx={toSvgX(pendingNode.x)} cy={toSvgY(pendingNode.y)} r={8}
                fill={getNodeColor(selectedNodeType)} opacity={0.5}
                stroke="#fff" strokeWidth={2} strokeDasharray="3,2"
              />
            )}
          </Svg>
        </View>

        {/* 범례 */}
        <View style={styles.legend}>
          {NODE_TYPES.map(t => (
            <View key={t.value} style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: t.color }]} />
              <Text style={styles.legendText}>{t.icon} {t.label}</Text>
            </View>
          ))}
        </View>

        {/* 통계 */}
        <View style={styles.stats}>
          <Text style={styles.statsText}>노드 {nodes.length}개 | 엣지 {edges.length}개</Text>
          <TouchableOpacity style={styles.refreshBtn} onPress={loadMapData}>
            <Text style={styles.refreshBtnText}>🔄 새로고침</Text>
          </TouchableOpacity>
        </View>

        {/* 노드 목록 */}
        <View style={styles.nodeList}>
          <Text style={styles.nodeListTitle}>노드 목록</Text>
          {nodes.map(n => {
            const typeInfo = NODE_TYPES.find(t => t.value === n.node_type);
            const connectedEdges = edges.filter(
              e => e.from_node_id === n.node_id || e.to_node_id === n.node_id
            );
            return (
              <View key={n.node_id} style={styles.nodeListItem}>
                <View style={[styles.nodeListDot, { backgroundColor: typeInfo?.color || '#b2bec3' }]} />
                <View style={styles.nodeListInfo}>
                  <Text style={styles.nodeListName}>
                    #{n.node_id} {n.label || typeInfo?.label}
                  </Text>
                  <Text style={styles.nodeListCoord}>
                    ({n.x}, {n.y}) · {connectedEdges.length}개 경로 연결
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        <View style={{ height: 30 }} />
      </ScrollView>

      {/* 노드 라벨 입력 모달 */}
      <Modal visible={labelModal} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>노드 추가</Text>
            <Text style={styles.modalSub}>
              좌표: ({pendingNode?.x}, {pendingNode?.y}) | 타입: {NODE_TYPES.find(t => t.value === selectedNodeType)?.label}
            </Text>
            <TextInput
              style={styles.modalInput}
              placeholder="라벨 (예: 음료 코너, 냉동식품, 통로1)"
              value={nodeLabel}
              onChangeText={setNodeLabel}
              autoFocus
            />
            <View style={styles.modalBtnRow}>
              <TouchableOpacity
                style={[styles.modalBtn, { backgroundColor: '#dfe6e9' }]}
                onPress={() => { setLabelModal(false); setPendingNode(null); }}
              >
                <Text style={{ color: '#636e72' }}>취소</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalBtn, { backgroundColor: '#0984e3' }]}
                onPress={confirmAddNode}
              >
                <Text style={{ color: '#fff', fontWeight: 'bold' }}>추가</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* 평면도 업로드 모달 */}
      <Modal visible={uploadModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { maxHeight: '85%' }]}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text style={styles.modalTitle}>평면도 업로드</Text>
              <TouchableOpacity onPress={() => setUploadModal(false)}>
                <Text style={{ fontSize: 20, color: '#636e72' }}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={{ marginTop: 12 }} showsVerticalScrollIndicator={false}>
              {/* 이미지 URL 입력 */}
              <Text style={styles.uploadSectionTitle}>이미지 URL로 업로드</Text>
              <Text style={styles.uploadSectionDesc}>
                PNG, JPG, SVG 형식의 매장 평면도 이미지 URL을 입력하세요
              </Text>
              <View style={{ flexDirection: 'row', gap: 8 }}>
                <TextInput
                  style={[styles.modalInput, { flex: 1 }]}
                  placeholder="https://example.com/floorplan.png"
                  value={imageUrlInput}
                  onChangeText={setImageUrlInput}
                  keyboardType="url"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                <TouchableOpacity
                  style={[styles.modalBtn, {
                    backgroundColor: uploadingImage ? '#b2bec3' : '#0984e3',
                    justifyContent: 'center', minWidth: 60,
                  }]}
                  onPress={handleUrlUpload}
                  disabled={uploadingImage}
                >
                  {uploadingImage
                    ? <ActivityIndicator size="small" color="#fff" />
                    : <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 13 }}>적용</Text>
                  }
                </TouchableOpacity>
              </View>

              {/* 구분선 */}
              <View style={styles.uploadDivider}>
                <View style={styles.uploadDividerLine} />
                <Text style={styles.uploadDividerText}>또는</Text>
                <View style={styles.uploadDividerLine} />
              </View>

              {/* 샘플 평면도 */}
              <Text style={styles.uploadSectionTitle}>샘플 평면도 선택</Text>
              <Text style={styles.uploadSectionDesc}>
                내장된 매장 레이아웃 템플릿을 선택하여 바로 편집을 시작할 수 있습니다
              </Text>
              {SAMPLE_FLOORPLANS.map(sample => {
                const isActive = selectedFloorplan?.id === sample.id;
                return (
                  <TouchableOpacity
                    key={sample.id}
                    style={[styles.sampleCard, isActive && styles.sampleCardActive]}
                    onPress={() => selectSampleFloorplan(sample)}
                  >
                    <Text style={styles.sampleThumb}>{sample.thumbnail}</Text>
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.sampleName, isActive && { color: '#0984e3' }]}>
                        {sample.name} {isActive ? '(적용 중)' : ''}
                      </Text>
                      <Text style={styles.sampleDesc}>{sample.desc}</Text>
                      <Text style={styles.sampleMeta}>
                        벽 {sample.walls.length}개 · 구역 {sample.zones.length}개
                      </Text>
                    </View>
                    <Text style={{ fontSize: 18, color: isActive ? '#0984e3' : '#b2bec3' }}>
                      {isActive ? '✓' : '→'}
                    </Text>
                  </TouchableOpacity>
                );
              })}

              {/* 지원 형식 안내 */}
              <View style={styles.formatInfo}>
                <Text style={styles.formatInfoTitle}>지원 형식 안내</Text>
                <Text style={styles.formatInfoText}>
                  {'• CAD 파일 (.dwg, .dxf) - AutoCAD 건축 도면\n'}
                  {'• PDF - 건축 설계 도면\n'}
                  {'• 이미지 (.png, .jpg) - 스캔된 도면/직접 촬영\n'}
                  {'• SVG - 벡터 도면\n\n'}
                  서버에 직접 업로드하려면 백엔드 API를 사용하세요:{'\n'}
                  POST /api/v1/route/floorplan/upload
                </Text>
              </View>

              <View style={{ height: 20 }} />
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 12, color: '#636e72' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 10, backgroundColor: '#2d3436',
  },
  title: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  uploadBtn: {
    backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 6,
  },
  uploadBtnText: { color: '#fff', fontSize: 12 },

  toolbar: {
    flexDirection: 'row', backgroundColor: '#fff', paddingVertical: 6,
    paddingHorizontal: 8, gap: 6, borderBottomWidth: 1, borderBottomColor: '#f1f2f6',
  },
  toolBtn: {
    flex: 1, alignItems: 'center', paddingVertical: 6, borderRadius: 8,
    backgroundColor: '#f8f9fa',
  },
  toolBtnActive: { backgroundColor: '#0984e3' },
  toolIcon: { fontSize: 18 },
  toolLabel: { fontSize: 10, color: '#636e72', marginTop: 2 },
  toolLabelActive: { color: '#fff', fontWeight: 'bold' },

  typeSelector: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: 10,
    paddingVertical: 6, backgroundColor: '#fff', flexWrap: 'wrap', gap: 4,
  },
  typeSelectorLabel: { fontSize: 12, color: '#636e72', marginRight: 4 },
  typeChip: {
    borderWidth: 1.5, borderColor: '#dfe6e9', borderRadius: 14,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  typeChipText: { fontSize: 11, color: '#2d3436' },

  hintBar: {
    backgroundColor: '#e8f4fd', paddingHorizontal: 14, paddingVertical: 6,
  },
  hintText: { fontSize: 12, color: '#0984e3', textAlign: 'center' },

  mapScroll: { paddingBottom: 20 },
  mapContainer: {
    marginHorizontal: MAP_PADDING, marginTop: 8,
    backgroundColor: '#fff', borderRadius: 12, padding: 4,
    shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 6, elevation: 3,
  },

  legend: {
    flexDirection: 'row', justifyContent: 'center', gap: 12,
    paddingVertical: 8, flexWrap: 'wrap',
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { fontSize: 10, color: '#636e72' },

  stats: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 6,
  },
  statsText: { fontSize: 12, color: '#636e72' },
  refreshBtn: { backgroundColor: '#f1f2f6', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4 },
  refreshBtnText: { fontSize: 12, color: '#2d3436' },

  nodeList: { marginHorizontal: 16, backgroundColor: '#fff', borderRadius: 12, padding: 12 },
  nodeListTitle: { fontSize: 14, fontWeight: 'bold', color: '#2d3436', marginBottom: 8 },
  nodeListItem: {
    flexDirection: 'row', alignItems: 'center', paddingVertical: 6,
    borderBottomWidth: 0.5, borderBottomColor: '#f1f2f6',
  },
  nodeListDot: { width: 12, height: 12, borderRadius: 6, marginRight: 10 },
  nodeListInfo: { flex: 1 },
  nodeListName: { fontSize: 13, fontWeight: '600', color: '#2d3436' },
  nodeListCoord: { fontSize: 11, color: '#636e72', marginTop: 1 },

  // 평면도 배지
  floorplanBadge: {
    backgroundColor: '#e8f4fd', paddingHorizontal: 14, paddingVertical: 4,
    borderBottomWidth: 1, borderBottomColor: '#d4ecf7',
  },
  floorplanBadgeText: { fontSize: 11, color: '#0984e3', textAlign: 'center', fontWeight: '600' },

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center', paddingHorizontal: 20,
  },
  modalContent: {
    backgroundColor: '#fff', borderRadius: 16, padding: 24,
  },
  modalTitle: { fontSize: 18, fontWeight: 'bold', color: '#2d3436' },
  modalSub: { fontSize: 12, color: '#636e72', marginTop: 4, marginBottom: 12 },
  modalInput: {
    backgroundColor: '#f1f2f6', borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 10, fontSize: 15,
  },
  modalBtnRow: {
    flexDirection: 'row', justifyContent: 'flex-end', gap: 10, marginTop: 16,
  },
  modalBtn: { borderRadius: 8, paddingHorizontal: 20, paddingVertical: 10, alignItems: 'center' },

  // 업로드 모달 스타일
  uploadSectionTitle: {
    fontSize: 14, fontWeight: 'bold', color: '#2d3436', marginBottom: 4,
  },
  uploadSectionDesc: {
    fontSize: 11, color: '#636e72', marginBottom: 10, lineHeight: 16,
  },
  uploadDivider: {
    flexDirection: 'row', alignItems: 'center', marginVertical: 16, gap: 10,
  },
  uploadDividerLine: { flex: 1, height: 1, backgroundColor: '#dfe6e9' },
  uploadDividerText: { fontSize: 12, color: '#b2bec3' },

  sampleCard: {
    flexDirection: 'row', alignItems: 'center', padding: 14,
    backgroundColor: '#f8f9fa', borderRadius: 12, marginBottom: 8,
    borderWidth: 1.5, borderColor: '#f1f2f6', gap: 12,
  },
  sampleCardActive: {
    borderColor: '#0984e3', backgroundColor: '#f0f8ff',
  },
  sampleThumb: { fontSize: 30 },
  sampleName: { fontSize: 14, fontWeight: 'bold', color: '#2d3436' },
  sampleDesc: { fontSize: 11, color: '#636e72', marginTop: 2 },
  sampleMeta: { fontSize: 10, color: '#b2bec3', marginTop: 2 },

  formatInfo: {
    backgroundColor: '#f8f9fa', borderRadius: 10, padding: 14, marginTop: 12,
    borderWidth: 1, borderColor: '#f1f2f6',
  },
  formatInfoTitle: { fontSize: 12, fontWeight: 'bold', color: '#636e72', marginBottom: 6 },
  formatInfoText: { fontSize: 11, color: '#636e72', lineHeight: 18 },
});
