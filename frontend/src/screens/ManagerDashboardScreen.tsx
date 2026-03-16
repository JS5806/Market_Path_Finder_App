/**
 * 마트 관리자 대시보드
 * - 상품/가격 관리
 * - ESL(전자 가격표) 업데이트
 * - 혼잡도 모니터링
 * - 결제 내역 관리
 */
import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Alert, RefreshControl, TextInput, Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore, getRoleLabel } from '../store/authStore';
import { productAPI, iotAPI, congestionAPI, paymentAPI } from '../services/api';
import { DEFAULT_STORE_ID, DEFAULT_STORE_NAME } from '../store/storeConfig';

export default function ManagerDashboardScreen() {
  const insets = useSafeAreaInsets();
  const { user, logout } = useAuthStore();
  const [refreshing, setRefreshing] = useState(false);
  const [products, setProducts] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [eslModalVisible, setEslModalVisible] = useState(false);

  // ESL 업데이트 폼
  const [eslMac, setEslMac] = useState('');
  const [eslProductName, setEslProductName] = useState('');
  const [eslPrice, setEslPrice] = useState('');
  const [eslSalePrice, setEslSalePrice] = useState('');

  const loadData = async () => {
    try {
      const [prodRes, txRes] = await Promise.all([
        productAPI.search({ store_id: DEFAULT_STORE_ID, page: 1, size: 10 }),
        paymentAPI.getTransactions(10).catch(() => ({ data: [] })),
      ]);
      setProducts(prodRes.data.items || []);
      setTransactions(txRes.data?.data || txRes.data || []);
    } catch {}
  };

  useEffect(() => { loadData(); }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleLogout = () => {
    Alert.alert('로그아웃', '로그아웃하시겠어요?', [
      { text: '취소', style: 'cancel' },
      { text: '로그아웃', onPress: () => logout() },
    ]);
  };

  // ESL 업데이트 실행
  const handleEslUpdate = async () => {
    if (!eslMac.trim() || !eslProductName.trim() || !eslPrice.trim()) {
      Alert.alert('알림', 'MAC 주소, 상품명, 가격을 모두 입력해주세요');
      return;
    }
    try {
      await iotAPI.updateEsl({
        mac_address: eslMac.trim(),
        product_name: eslProductName.trim(),
        regular_price: parseInt(eslPrice),
        sale_price: eslSalePrice ? parseInt(eslSalePrice) : undefined,
        store_name: DEFAULT_STORE_NAME,
      });
      Alert.alert('성공', 'ESL 업데이트 명령을 전송했습니다');
      setEslModalVisible(false);
      setEslMac(''); setEslProductName(''); setEslPrice(''); setEslSalePrice('');
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'ESL 업데이트에 실패했습니다';
      Alert.alert('오류', msg);
    }
  };

  const isSaleProduct = (p: any) =>
    p.sale_price && p.sale_price > 0 && p.sale_price < p.regular_price;

  return (
    <ScrollView
      style={[styles.container, { paddingTop: insets.top }]}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* 헤더 */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>매장 관리</Text>
          <Text style={styles.headerSub}>
            {user?.user_name} ({getRoleLabel(user?.role || 'manager')}) · {DEFAULT_STORE_NAME}
          </Text>
        </View>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutBtnText}>로그아웃</Text>
        </TouchableOpacity>
      </View>

      {/* 빠른 액션 */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={[styles.quickBtn, { backgroundColor: '#0984e3' }]}
          onPress={() => setEslModalVisible(true)}
        >
          <Text style={styles.quickIcon}>📟</Text>
          <Text style={styles.quickLabel}>ESL 업데이트</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.quickBtn, { backgroundColor: '#00b894' }]}
          onPress={async () => {
            try {
              await congestionAPI.simulate(DEFAULT_STORE_ID);
              Alert.alert('알림', '혼잡도 시뮬레이션이 실행되었습니다');
            } catch {
              Alert.alert('오류', '혼잡도 시뮬레이션 실패');
            }
          }}
        >
          <Text style={styles.quickIcon}>📊</Text>
          <Text style={styles.quickLabel}>혼잡도 체크</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.quickBtn, { backgroundColor: '#6c5ce7' }]}
          onPress={() => Alert.alert('상품 등록', '새 상품 등록 기능 (개발 중)')}
        >
          <Text style={styles.quickIcon}>📦</Text>
          <Text style={styles.quickLabel}>상품 등록</Text>
        </TouchableOpacity>
      </View>

      {/* 상품 현황 */}
      <Text style={styles.sectionTitle}>상품 현황 (최근 10개)</Text>
      <View style={styles.card}>
        {products.length === 0 ? (
          <Text style={styles.emptyText}>상품 데이터가 없습니다</Text>
        ) : (
          products.map((p: any, idx: number) => (
            <View key={p.product_id || idx} style={styles.productRow}>
              <View style={styles.productInfo}>
                <Text style={styles.productName} numberOfLines={1}>{p.product_name}</Text>
                <Text style={styles.productSpec}>{p.manufacturer} | {p.specification}</Text>
              </View>
              <View style={styles.priceCol}>
                {isSaleProduct(p) ? (
                  <>
                    <Text style={styles.origPrice}>{p.regular_price?.toLocaleString()}원</Text>
                    <Text style={styles.salePrice}>{p.sale_price?.toLocaleString()}원</Text>
                  </>
                ) : (
                  <Text style={styles.normalPrice}>
                    {p.regular_price?.toLocaleString() || '가격 미설정'}원
                  </Text>
                )}
              </View>
              {isSaleProduct(p) && (
                <View style={styles.saleBadge}>
                  <Text style={styles.saleBadgeText}>행사</Text>
                </View>
              )}
            </View>
          ))
        )}
      </View>

      {/* 최근 결제 */}
      <Text style={styles.sectionTitle}>최근 결제 내역</Text>
      <View style={styles.card}>
        {transactions.length === 0 ? (
          <Text style={styles.emptyText}>결제 내역이 없습니다</Text>
        ) : (
          transactions.slice(0, 5).map((tx: any, idx: number) => (
            <View key={tx.transaction_id || idx} style={styles.txRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.txAmount}>{tx.total_amount?.toLocaleString()}원</Text>
                <Text style={styles.txDate}>{tx.paid_at || tx.created_at}</Text>
              </View>
              <View style={[styles.txBadge, tx.status === 'paid' ? styles.txPaid : styles.txPending]}>
                <Text style={styles.txBadgeText}>
                  {tx.status === 'paid' ? '완료' : '대기'}
                </Text>
              </View>
            </View>
          ))
        )}
      </View>

      {/* 관리 메뉴 */}
      <Text style={styles.sectionTitle}>관리 메뉴</Text>
      <View style={styles.menuList}>
        {[
          { icon: '💰', label: '가격 일괄 변경', desc: '행사 상품 가격 일괄 설정' },
          { icon: '📟', label: 'ESL 일괄 업데이트', desc: '전체 ESL 장치 가격표 동기화' },
          { icon: '🏷️', label: 'NFC 태그 관리', desc: 'NFC 태그-상품 매핑 관리' },
          { icon: '📈', label: '매출 리포트', desc: '일별/주별 매출 통계 확인' },
        ].map((item, idx) => (
          <TouchableOpacity
            key={idx}
            style={styles.menuItem}
            onPress={() => Alert.alert(item.label, `${item.desc}\n(개발 중)`)}
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

      {/* ESL 업데이트 모달 */}
      <Modal visible={eslModalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>ESL 가격표 업데이트</Text>
              <TouchableOpacity onPress={() => setEslModalVisible(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalForm}>
              <Text style={styles.inputLabel}>ESP32 MAC 주소</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="AA:BB:CC:DD:EE:FF"
                value={eslMac}
                onChangeText={setEslMac}
                autoCapitalize="characters"
              />

              <Text style={styles.inputLabel}>상품명</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="국내산 삼겹살"
                value={eslProductName}
                onChangeText={setEslProductName}
              />

              <Text style={styles.inputLabel}>정가 (원)</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="15900"
                value={eslPrice}
                onChangeText={setEslPrice}
                keyboardType="numeric"
              />

              <Text style={styles.inputLabel}>할인가 (원, 선택)</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="12720 (비워두면 할인 없음)"
                value={eslSalePrice}
                onChangeText={setEslSalePrice}
                keyboardType="numeric"
              />

              <TouchableOpacity style={styles.eslSubmitBtn} onPress={handleEslUpdate}>
                <Text style={styles.eslSubmitText}>MQTT 전송 (ESL 업데이트)</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 16,
    backgroundColor: '#e17055',
  },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  headerSub: { color: '#ffddd2', fontSize: 12, marginTop: 2 },
  logoutBtn: {
    backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 6,
  },
  logoutBtnText: { color: '#fff', fontSize: 13 },

  quickActions: {
    flexDirection: 'row', paddingHorizontal: 16, paddingVertical: 16, gap: 10,
  },
  quickBtn: {
    flex: 1, borderRadius: 12, padding: 14, alignItems: 'center',
  },
  quickIcon: { fontSize: 28, marginBottom: 4 },
  quickLabel: { color: '#fff', fontSize: 12, fontWeight: 'bold' },

  sectionTitle: {
    fontSize: 16, fontWeight: 'bold', color: '#2d3436',
    paddingHorizontal: 20, paddingTop: 12, paddingBottom: 8,
  },
  card: {
    marginHorizontal: 16, backgroundColor: '#fff', borderRadius: 12, padding: 12,
  },
  emptyText: { textAlign: 'center', color: '#b2bec3', paddingVertical: 20 },

  productRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 10, borderBottomWidth: 0.5, borderBottomColor: '#f1f2f6',
  },
  productInfo: { flex: 1 },
  productName: { fontSize: 14, fontWeight: '600', color: '#2d3436' },
  productSpec: { fontSize: 11, color: '#636e72', marginTop: 2 },
  priceCol: { alignItems: 'flex-end', marginRight: 8 },
  origPrice: { fontSize: 11, color: '#b2bec3', textDecorationLine: 'line-through' },
  salePrice: { fontSize: 13, fontWeight: 'bold', color: '#d63031' },
  normalPrice: { fontSize: 13, fontWeight: '600', color: '#2d3436' },
  saleBadge: {
    backgroundColor: '#d63031', borderRadius: 6,
    paddingHorizontal: 6, paddingVertical: 2,
  },
  saleBadgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },

  txRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 10, borderBottomWidth: 0.5, borderBottomColor: '#f1f2f6',
  },
  txAmount: { fontSize: 15, fontWeight: 'bold', color: '#2d3436' },
  txDate: { fontSize: 11, color: '#636e72', marginTop: 2 },
  txBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  txPaid: { backgroundColor: '#00b89420' },
  txPending: { backgroundColor: '#fdcb6e40' },
  txBadgeText: { fontSize: 11, fontWeight: '600' },

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

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 24,
  },
  modalHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#2d3436' },
  modalClose: { fontSize: 20, color: '#636e72', padding: 4 },
  modalForm: { gap: 8 },
  inputLabel: { fontSize: 13, fontWeight: '600', color: '#2d3436', marginTop: 4 },
  modalInput: {
    backgroundColor: '#f1f2f6', borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 10, fontSize: 15,
  },
  eslSubmitBtn: {
    backgroundColor: '#e17055', borderRadius: 12,
    paddingVertical: 14, alignItems: 'center', marginTop: 12,
  },
  eslSubmitText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
});
