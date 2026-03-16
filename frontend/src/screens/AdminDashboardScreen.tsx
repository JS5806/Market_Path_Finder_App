/**
 * 프로그램 관리자 대시보드
 * - 시스템 상태 모니터링
 * - 매장 관리 (목록/등록)
 * - IoT 장치 대시보드
 * - 사용자 관리
 */
import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Alert, RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuthStore, getRoleLabel } from '../store/authStore';
import { iotAPI, congestionAPI } from '../services/api';
import { DEFAULT_STORE_ID, DEFAULT_STORE_NAME } from '../store/storeConfig';

export default function AdminDashboardScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const { user, logout } = useAuthStore();
  const [refreshing, setRefreshing] = useState(false);
  const [iotStatus, setIotStatus] = useState<any>(null);
  const [congestion, setCongestion] = useState<any>(null);

  const loadDashboard = async () => {
    try {
      const [iotRes, congRes] = await Promise.all([
        iotAPI.getDashboard(DEFAULT_STORE_ID).catch(() => ({ data: null })),
        congestionAPI.getSummary(DEFAULT_STORE_ID).catch(() => ({ data: null })),
      ]);
      setIotStatus(iotRes.data?.data || iotRes.data);
      setCongestion(congRes.data?.data || congRes.data);
    } catch {}
  };

  useEffect(() => { loadDashboard(); }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboard();
    setRefreshing(false);
  };

  const handleLogout = () => {
    Alert.alert('로그아웃', '로그아웃하시겠어요?', [
      { text: '취소', style: 'cancel' },
      { text: '로그아웃', onPress: () => logout() },
    ]);
  };

  return (
    <ScrollView
      style={[styles.container, { paddingTop: insets.top }]}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* 헤더 */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>시스템 관리</Text>
          <Text style={styles.headerSub}>
            {user?.user_name} ({getRoleLabel(user?.role || 'admin')})
          </Text>
        </View>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutBtnText}>로그아웃</Text>
        </TouchableOpacity>
      </View>

      {/* 시스템 상태 카드 */}
      <Text style={styles.sectionTitle}>시스템 상태</Text>
      <View style={styles.cardRow}>
        <View style={[styles.statusCard, { backgroundColor: '#00b894' }]}>
          <Text style={styles.cardIcon}>🖥️</Text>
          <Text style={styles.cardLabel}>서버</Text>
          <Text style={styles.cardValue}>정상</Text>
        </View>
        <View style={[styles.statusCard, { backgroundColor: '#0984e3' }]}>
          <Text style={styles.cardIcon}>📡</Text>
          <Text style={styles.cardLabel}>MQTT</Text>
          <Text style={styles.cardValue}>연결됨</Text>
        </View>
        <View style={[styles.statusCard, { backgroundColor: '#6c5ce7' }]}>
          <Text style={styles.cardIcon}>🗄️</Text>
          <Text style={styles.cardLabel}>DB</Text>
          <Text style={styles.cardValue}>정상</Text>
        </View>
      </View>

      {/* 매장 정보 */}
      <Text style={styles.sectionTitle}>매장 관리</Text>
      <View style={styles.card}>
        <View style={styles.cardRowInner}>
          <Text style={styles.cardItemLabel}>현재 매장</Text>
          <Text style={styles.cardItemValue}>{DEFAULT_STORE_NAME}</Text>
        </View>
        <View style={styles.cardRowInner}>
          <Text style={styles.cardItemLabel}>매장 ID</Text>
          <Text style={styles.cardItemValueSmall}>{DEFAULT_STORE_ID.substring(0, 8)}...</Text>
        </View>
      </View>

      {/* IoT 장치 현황 */}
      <Text style={styles.sectionTitle}>IoT 장치 현황</Text>
      <View style={styles.card}>
        <View style={styles.cardRowInner}>
          <Text style={styles.cardItemLabel}>비콘 (iBeacon)</Text>
          <Text style={styles.cardItemValue}>
            {iotStatus?.beacon_count ?? '–'}대
          </Text>
        </View>
        <View style={styles.cardRowInner}>
          <Text style={styles.cardItemLabel}>NFC 태그</Text>
          <Text style={styles.cardItemValue}>
            {iotStatus?.nfc_tag_count ?? '–'}개
          </Text>
        </View>
        <View style={styles.cardRowInner}>
          <Text style={styles.cardItemLabel}>ESL (전자 가격표)</Text>
          <Text style={styles.cardItemValue}>
            {iotStatus?.esl_count ?? '–'}대
          </Text>
        </View>
        <TouchableOpacity
          style={styles.actionBtn}
          onPress={() => Alert.alert('IoT 대시보드', 'IoT 장치 상세 관리 페이지로 이동합니다 (개발 중)')}
        >
          <Text style={styles.actionBtnText}>IoT 대시보드 열기</Text>
        </TouchableOpacity>
      </View>

      {/* 혼잡도 */}
      <Text style={styles.sectionTitle}>매장 혼잡도</Text>
      <View style={styles.card}>
        <View style={styles.cardRowInner}>
          <Text style={styles.cardItemLabel}>현재 혼잡도</Text>
          <Text style={[styles.cardItemValue, { color: '#e17055' }]}>
            {congestion?.avg_density ? `${(congestion.avg_density * 100).toFixed(0)}%` : '데이터 없음'}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.actionBtn}
          onPress={async () => {
            try {
              await congestionAPI.simulate(DEFAULT_STORE_ID);
              Alert.alert('시뮬레이션', '혼잡도 시뮬레이션이 실행되었습니다');
              loadDashboard();
            } catch {
              Alert.alert('오류', '시뮬레이션 실행에 실패했습니다');
            }
          }}
        >
          <Text style={styles.actionBtnText}>혼잡도 시뮬레이션 실행</Text>
        </TouchableOpacity>
      </View>

      {/* 관리 메뉴 */}
      <Text style={styles.sectionTitle}>관리 메뉴</Text>
      <View style={styles.menuList}>
        {[
          { icon: '🏪', label: '매장 등록/수정', desc: '새 매장 추가 및 기존 매장 정보 변경' },
          { icon: '📊', label: '사용 통계', desc: '일별/주별 사용자 및 매출 통계' },
          { icon: '👥', label: '사용자 관리', desc: '등록된 사용자 목록 및 권한 관리' },
          { icon: '🗺️', label: '매장 레이아웃 편집', desc: '노드/간선 편집, 상품 배치 변경' },
          { icon: '🔧', label: '시스템 설정', desc: 'API 키, MQTT 설정, 서버 설정' },
        ].map((item, idx) => (
          <TouchableOpacity
            key={idx}
            style={styles.menuItem}
            onPress={() => {
              if (item.label === '매장 레이아웃 편집') {
                navigation.navigate('MapEditorTab');
              } else {
                Alert.alert(item.label, `${item.desc}\n(개발 중)`);
              }
            }}
          >
            <Text style={styles.menuIcon}>{item.icon}</Text>
            <View style={styles.menuInfo}>
              <Text style={styles.menuLabel}>{item.label}</Text>
              <Text style={styles.menuDesc}>{item.desc}</Text>
            </View>
            <Text style={styles.menuArrow}>›</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={{ height: 30 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 16,
    backgroundColor: '#d63031',
  },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  headerSub: { color: '#ffdddd', fontSize: 13, marginTop: 2 },
  logoutBtn: {
    backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 6,
  },
  logoutBtnText: { color: '#fff', fontSize: 13 },
  sectionTitle: {
    fontSize: 16, fontWeight: 'bold', color: '#2d3436',
    paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8,
  },
  cardRow: {
    flexDirection: 'row', paddingHorizontal: 16, gap: 10,
  },
  statusCard: {
    flex: 1, borderRadius: 12, padding: 14, alignItems: 'center',
  },
  cardIcon: { fontSize: 28, marginBottom: 4 },
  cardLabel: { fontSize: 12, color: 'rgba(255,255,255,0.8)' },
  cardValue: { fontSize: 14, fontWeight: 'bold', color: '#fff', marginTop: 2 },
  card: {
    marginHorizontal: 16, backgroundColor: '#fff', borderRadius: 12, padding: 16,
  },
  cardRowInner: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 10, borderBottomWidth: 0.5, borderBottomColor: '#f1f2f6',
  },
  cardItemLabel: { fontSize: 14, color: '#2d3436' },
  cardItemValue: { fontSize: 14, fontWeight: 'bold', color: '#2d3436' },
  cardItemValueSmall: { fontSize: 12, color: '#636e72', fontFamily: 'monospace' },
  actionBtn: {
    backgroundColor: '#0984e3', borderRadius: 8,
    paddingVertical: 10, alignItems: 'center', marginTop: 12,
  },
  actionBtnText: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  menuList: { marginHorizontal: 16, backgroundColor: '#fff', borderRadius: 12 },
  menuItem: {
    flexDirection: 'row', alignItems: 'center', padding: 16,
    borderBottomWidth: 0.5, borderBottomColor: '#f1f2f6',
  },
  menuIcon: { fontSize: 28, marginRight: 12 },
  menuInfo: { flex: 1 },
  menuLabel: { fontSize: 15, fontWeight: '600', color: '#2d3436' },
  menuDesc: { fontSize: 12, color: '#636e72', marginTop: 2 },
  menuArrow: { fontSize: 22, color: '#b2bec3' },
});
