/**
 * 장바구니 화면 - QR 결제 기능 포함
 * SafeArea 적용 + 수량 +/- 컨트롤 + 단가/소계/합계 표시
 */
import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, Alert,
  ActivityIndicator, Modal, ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useCartStore } from '../store/cartStore';
import { routeAPI, paymentAPI } from '../services/api';
import { DEFAULT_STORE_ID } from '../store/storeConfig';

export default function CartScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const { items, totalPrice, itemCount, sessionId, isLoading, fetchCart, updateQuantity, removeItem, clearCart } = useCartStore();
  const [qrModalVisible, setQrModalVisible] = useState(false);
  const [qrData, setQrData] = useState<any>(null);
  const [paymentLoading, setPaymentLoading] = useState(false);

  useEffect(() => {
    fetchCart();
  }, []);

  // 수량 변경
  const handleQuantityChange = (itemId: number, currentQty: number, delta: number) => {
    const newQty = currentQty + delta;
    if (newQty <= 0) {
      // 0 이하면 삭제 확인
      const item = items.find(i => i.item_id === itemId);
      Alert.alert('삭제 확인', `${item?.product_name || '상품'}을(를) 장바구니에서 제거할까요?`, [
        { text: '취소', style: 'cancel' },
        { text: '삭제', style: 'destructive', onPress: () => removeItem(itemId) },
      ]);
      return;
    }
    updateQuantity(itemId, newQty);
  };

  const handleRemove = (itemId: number, name: string) => {
    Alert.alert('삭제 확인', `${name}을(를) 장바구니에서 제거할까요?`, [
      { text: '취소', style: 'cancel' },
      { text: '삭제', style: 'destructive', onPress: () => removeItem(itemId) },
    ]);
  };

  const handleClearAll = () => {
    Alert.alert('전체 비우기', '장바구니를 모두 비울까요?', [
      { text: '취소', style: 'cancel' },
      { text: '비우기', style: 'destructive', onPress: () => clearCart() },
    ]);
  };

  const handleOptimizeRoute = async () => {
    if (items.length === 0) {
      Alert.alert('알림', '장바구니에 상품을 먼저 추가해주세요');
      return;
    }
    try {
      const res = await routeAPI.optimizeFromCart({ store_id: DEFAULT_STORE_ID });
      const routeData = res.data.data || res.data;
      navigation.navigate('RouteTab', {
        screen: 'RouteMap',
        params: { routeData },
      });
    } catch (e: any) {
      Alert.alert('오류', '경로 계산에 실패했습니다');
    }
  };

  // QR 결제 생성
  const handlePayment = async () => {
    if (items.length === 0) {
      Alert.alert('알림', '장바구니에 상품을 먼저 추가해주세요');
      return;
    }
    if (!sessionId) {
      Alert.alert('오류', '장바구니 세션이 없습니다. 상품을 다시 추가해주세요.');
      return;
    }

    setPaymentLoading(true);
    try {
      const res = await paymentAPI.generateQr({
        session_id: sessionId,
        store_id: DEFAULT_STORE_ID,
      });
      const data = res.data;
      setQrData(data);
      setQrModalVisible(true);
    } catch (e: any) {
      const msg = e.response?.data?.detail || '결제 생성에 실패했습니다';
      Alert.alert('오류', msg);
    } finally {
      setPaymentLoading(false);
    }
  };

  // 결제 승인 (데모용 - POS 시뮬레이션)
  const handleConfirmPayment = async () => {
    if (!qrData) return;
    try {
      const res = await paymentAPI.confirm({
        transaction_id: qrData.transaction_id,
        approval_number: `POS-${Date.now()}`,
      });
      setQrModalVisible(false);
      setQrData(null);
      Alert.alert('결제 완료!', `승인번호: ${res.data.approval_number}\n금액: ${res.data.total_amount.toLocaleString()}원`, [
        { text: '확인', onPress: () => { clearCart(); fetchCart(); } },
      ]);
    } catch (e: any) {
      const msg = e.response?.data?.detail || '결제 승인에 실패했습니다';
      Alert.alert('오류', msg);
    }
  };

  // 소계 계산 (unit_price * quantity)
  const getLineTotal = (item: any) => {
    if (item.unit_price > 0) return item.unit_price * item.quantity;
    return 0;
  };

  // 합계 계산 (totalPrice가 0이면 직접 계산)
  const grandTotal = totalPrice > 0
    ? totalPrice
    : items.reduce((sum, item) => sum + getLineTotal(item), 0);

  const renderItem = ({ item }: { item: any }) => (
    <View style={styles.cartItem}>
      <View style={styles.itemInfo}>
        <Text style={styles.itemName}>{item.product_name || '상품'}</Text>
        <Text style={styles.itemDetail}>
          {item.source === 'ai' ? 'AI 추천' : '수동 추가'}
        </Text>
        {/* 단가 표시 */}
        {item.unit_price > 0 && (
          <Text style={styles.unitPrice}>
            단가: {item.unit_price.toLocaleString()}원
          </Text>
        )}
      </View>

      {/* 수량 +/- 컨트롤 */}
      <View style={styles.quantityControl}>
        <TouchableOpacity
          style={styles.qtyButton}
          onPress={() => handleQuantityChange(item.item_id, item.quantity, -1)}
        >
          <Text style={styles.qtyButtonText}>-</Text>
        </TouchableOpacity>
        <Text style={styles.qtyText}>{item.quantity}</Text>
        <TouchableOpacity
          style={styles.qtyButton}
          onPress={() => handleQuantityChange(item.item_id, item.quantity, 1)}
        >
          <Text style={styles.qtyButtonText}>+</Text>
        </TouchableOpacity>
      </View>

      {/* 소계 (라인 합계) */}
      <View style={styles.lineTotalContainer}>
        {item.unit_price > 0 && (
          <Text style={styles.lineTotal}>
            {getLineTotal(item).toLocaleString()}원
          </Text>
        )}
        <TouchableOpacity
          style={styles.removeButton}
          onPress={() => handleRemove(item.item_id, item.product_name)}
        >
          <Text style={styles.removeText}>✕</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (isLoading) {
    return (
      <View style={[styles.center, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* 헤더 */}
      <View style={styles.header}>
        <Text style={styles.title}>장바구니</Text>
        {items.length > 0 && (
          <TouchableOpacity onPress={handleClearAll}>
            <Text style={styles.clearText}>전체 삭제</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* 상품 목록 */}
      <FlatList
        data={items}
        renderItem={renderItem}
        keyExtractor={(item) => String(item.item_id)}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🛒</Text>
            <Text style={styles.emptyText}>장바구니가 비어있어요</Text>
            <Text style={styles.emptySubtext}>상품을 검색해서 추가해보세요!</Text>
          </View>
        }
      />

      {/* 하단 요약 + 버튼들 */}
      {items.length > 0 && (
        <View style={[styles.footer, { paddingBottom: Math.max(insets.bottom, 16) }]}>
          <View style={styles.summary}>
            <Text style={styles.summaryText}>총 {itemCount}개 상품</Text>
            <Text style={styles.totalPrice}>{grandTotal.toLocaleString()}원</Text>
          </View>
          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.routeButton} onPress={handleOptimizeRoute}>
              <Text style={styles.routeButtonText}>🗺️ 최적 경로</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.payButton}
              onPress={handlePayment}
              disabled={paymentLoading}
            >
              {paymentLoading ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.payButtonText}>💳 QR 결제</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* QR 결제 모달 */}
      <Modal visible={qrModalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>QR 결제</Text>

            {qrData && (
              <ScrollView style={styles.qrInfo}>
                <Text style={styles.qrAmount}>
                  {qrData.total_amount?.toLocaleString()}원
                </Text>
                <Text style={styles.qrCount}>
                  {qrData.item_count}개 상품
                </Text>
                <View style={styles.qrBox}>
                  <Text style={styles.qrPlaceholder}>📱</Text>
                  <Text style={styles.qrGuide}>POS에서 이 QR을 스캔하세요</Text>
                  <Text style={styles.qrTxId}>
                    거래ID: {qrData.transaction_id?.substring(0, 8)}...
                  </Text>
                </View>
              </ScrollView>
            )}

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.confirmButton}
                onPress={handleConfirmPayment}
              >
                <Text style={styles.confirmButtonText}>결제 승인 (데모)</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => { setQrModalVisible(false); setQrData(null); }}
              >
                <Text style={styles.cancelButtonText}>취소</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 14, backgroundColor: '#fff',
  },
  title: { fontSize: 20, fontWeight: 'bold', color: '#2d3436' },
  clearText: { color: '#d63031', fontSize: 14 },
  list: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 180 },
  cartItem: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#fff', borderRadius: 12, padding: 14, marginBottom: 8,
  },
  itemInfo: { flex: 1, marginRight: 8 },
  itemName: { fontSize: 15, fontWeight: '600', color: '#2d3436' },
  itemDetail: { fontSize: 11, color: '#636e72', marginTop: 2 },
  unitPrice: { fontSize: 12, color: '#0984e3', marginTop: 2 },

  // 수량 컨트롤
  quantityControl: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#f1f2f6', borderRadius: 8,
    marginRight: 10,
  },
  qtyButton: {
    width: 32, height: 32,
    justifyContent: 'center', alignItems: 'center',
  },
  qtyButtonText: { fontSize: 18, fontWeight: 'bold', color: '#2d3436' },
  qtyText: {
    fontSize: 14, fontWeight: 'bold', color: '#2d3436',
    minWidth: 24, textAlign: 'center',
  },

  // 소계 + 삭제
  lineTotalContainer: { alignItems: 'flex-end', minWidth: 70 },
  lineTotal: { fontSize: 14, fontWeight: 'bold', color: '#2d3436', marginBottom: 4 },
  removeButton: {
    width: 26, height: 26, borderRadius: 13,
    backgroundColor: '#ffeaa7', justifyContent: 'center', alignItems: 'center',
  },
  removeText: { fontSize: 12, color: '#d63031' },

  emptyContainer: { alignItems: 'center', paddingTop: 60 },
  emptyIcon: { fontSize: 64, marginBottom: 16 },
  emptyText: { fontSize: 18, fontWeight: 'bold', color: '#b2bec3' },
  emptySubtext: { fontSize: 14, color: '#b2bec3', marginTop: 4 },
  footer: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    backgroundColor: '#fff', paddingHorizontal: 20, paddingTop: 16,
    borderTopWidth: 1, borderTopColor: '#dfe6e9',
  },
  summary: {
    flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12,
  },
  summaryText: { fontSize: 14, color: '#636e72' },
  totalPrice: { fontSize: 20, fontWeight: 'bold', color: '#2d3436' },
  buttonRow: { flexDirection: 'row', gap: 10 },
  routeButton: {
    flex: 1, backgroundColor: '#00b894', borderRadius: 12,
    paddingVertical: 14, alignItems: 'center',
  },
  routeButtonText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
  payButton: {
    flex: 1, backgroundColor: '#0984e3', borderRadius: 12,
    paddingVertical: 14, alignItems: 'center',
  },
  payButtonText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 24, minHeight: 400,
  },
  modalTitle: { fontSize: 22, fontWeight: 'bold', color: '#2d3436', textAlign: 'center' },
  qrInfo: { marginTop: 20 },
  qrAmount: { fontSize: 32, fontWeight: 'bold', color: '#2d3436', textAlign: 'center' },
  qrCount: { fontSize: 14, color: '#636e72', textAlign: 'center', marginTop: 4 },
  qrBox: {
    backgroundColor: '#f8f9fa', borderRadius: 16, padding: 30,
    alignItems: 'center', marginTop: 20,
  },
  qrPlaceholder: { fontSize: 80 },
  qrGuide: { fontSize: 14, color: '#636e72', marginTop: 10 },
  qrTxId: { fontSize: 11, color: '#b2bec3', marginTop: 8 },
  modalButtons: { marginTop: 20 },
  confirmButton: {
    backgroundColor: '#0984e3', borderRadius: 12,
    paddingVertical: 16, alignItems: 'center', marginBottom: 10,
  },
  confirmButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  cancelButton: {
    backgroundColor: '#dfe6e9', borderRadius: 12,
    paddingVertical: 16, alignItems: 'center',
  },
  cancelButtonText: { color: '#636e72', fontSize: 16 },
});
