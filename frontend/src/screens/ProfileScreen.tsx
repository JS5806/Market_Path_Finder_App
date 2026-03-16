/**
 * 프로필 / 설정 / 쇼핑 히스토리 화면
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Alert,
  FlatList, ActivityIndicator, Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore, getRoleLabel } from '../store/authStore';
import { paymentAPI } from '../services/api';
import { DEFAULT_STORE_NAME } from '../store/storeConfig';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const { user, logout } = useAuthStore();
  const [historyVisible, setHistoryVisible] = useState(false);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const handleLogout = () => {
    Alert.alert('로그아웃', '로그아웃하시겠어요?', [
      { text: '취소', style: 'cancel' },
      { text: '로그아웃', onPress: () => logout() },
    ]);
  };

  const handleShowHistory = async () => {
    setHistoryVisible(true);
    setHistoryLoading(true);
    try {
      const res = await paymentAPI.getTransactions(20);
      setTransactions(res.data || []);
    } catch {
      setTransactions([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
  };

  const statusLabel = (status: string) => {
    if (status === 'paid') return '결제완료';
    if (status === 'pending') return '대기중';
    return status;
  };

  const renderTransaction = ({ item }: { item: any }) => (
    <View style={styles.txItem}>
      <View style={styles.txInfo}>
        <Text style={styles.txAmount}>{item.total_amount?.toLocaleString()}원</Text>
        <Text style={styles.txDate}>
          {item.paid_at ? formatDate(item.paid_at) : formatDate(item.created_at)}
        </Text>
      </View>
      <View style={[styles.txBadge, item.status === 'paid' ? styles.txPaid : styles.txPending]}>
        <Text style={styles.txBadgeText}>{statusLabel(item.status)}</Text>
      </View>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* 프로필 카드 */}
      <View style={styles.profileCard}>
        <Text style={styles.avatar}>
          {user?.role === 'admin' ? '🛡️' : user?.role === 'manager' ? '🏪' : '👤'}
        </Text>
        <Text style={styles.userName}>{user?.user_name || '사용자'}</Text>
        <Text style={styles.email}>{user?.email || ''}</Text>
        {user?.role && (
          <View style={[styles.roleBadge, {
            backgroundColor: user.role === 'admin' ? '#d63031' :
                             user.role === 'manager' ? '#e17055' : '#00b894',
          }]}>
            <Text style={styles.roleBadgeText}>{getRoleLabel(user.role)}</Text>
          </View>
        )}
      </View>

      {/* 메뉴 */}
      <View style={styles.menuGroup}>
        <View style={styles.menuItem}>
          <Text style={styles.menuLabel}>기본 매장</Text>
          <Text style={styles.menuValue}>📍 {DEFAULT_STORE_NAME}</Text>
        </View>
        <View style={styles.menuItem}>
          <Text style={styles.menuLabel}>연령대</Text>
          <Text style={styles.menuValue}>{user?.age_group || '미설정'}</Text>
        </View>
      </View>

      <View style={styles.menuGroup}>
        <TouchableOpacity style={styles.menuItem} onPress={handleShowHistory}>
          <Text style={styles.menuLabel}>결제 내역</Text>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuLabel}>알림 설정</Text>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.menuGroup}>
        <View style={styles.menuItem}>
          <Text style={styles.menuLabel}>앱 버전</Text>
          <Text style={styles.menuValue}>0.3.0 (개발 중)</Text>
        </View>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>로그아웃</Text>
      </TouchableOpacity>

      {/* 거래 내역 모달 */}
      <Modal visible={historyVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>결제 내역</Text>
              <TouchableOpacity onPress={() => setHistoryVisible(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            {historyLoading ? (
              <ActivityIndicator size="large" style={{ marginTop: 40 }} />
            ) : transactions.length === 0 ? (
              <View style={styles.emptyHistory}>
                <Text style={styles.emptyText}>결제 내역이 없습니다</Text>
              </View>
            ) : (
              <FlatList
                data={transactions}
                renderItem={renderTransaction}
                keyExtractor={(item) => item.transaction_id}
                contentContainerStyle={{ paddingBottom: 20 }}
              />
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  profileCard: {
    alignItems: 'center', backgroundColor: '#fff',
    paddingVertical: 30, marginBottom: 8,
  },
  avatar: { fontSize: 60, marginBottom: 10 },
  userName: { fontSize: 20, fontWeight: 'bold', color: '#2d3436' },
  email: { fontSize: 14, color: '#636e72', marginTop: 4 },
  roleBadge: {
    marginTop: 8, borderRadius: 12,
    paddingHorizontal: 12, paddingVertical: 4,
  },
  roleBadgeText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  menuGroup: { backgroundColor: '#fff', marginBottom: 8 },
  menuItem: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 16,
    borderBottomWidth: 0.5, borderBottomColor: '#f1f2f6',
  },
  menuLabel: { fontSize: 15, color: '#2d3436' },
  menuValue: { fontSize: 14, color: '#636e72' },
  menuArrow: { fontSize: 20, color: '#b2bec3' },
  logoutButton: {
    marginHorizontal: 20, marginTop: 20,
    backgroundColor: '#fff', borderRadius: 12,
    paddingVertical: 16, alignItems: 'center',
    borderWidth: 1, borderColor: '#d63031',
  },
  logoutText: { color: '#d63031', fontSize: 16, fontWeight: 'bold' },

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 20, maxHeight: '70%',
  },
  modalHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#2d3436' },
  modalClose: { fontSize: 20, color: '#636e72', padding: 4 },
  txItem: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: '#f1f2f6',
  },
  txInfo: { flex: 1 },
  txAmount: { fontSize: 16, fontWeight: 'bold', color: '#2d3436' },
  txDate: { fontSize: 12, color: '#636e72', marginTop: 2 },
  txBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  txPaid: { backgroundColor: '#00b89420' },
  txPending: { backgroundColor: '#fdcb6e40' },
  txBadgeText: { fontSize: 12, fontWeight: '600' },
  emptyHistory: { alignItems: 'center', paddingTop: 40 },
  emptyText: { fontSize: 16, color: '#b2bec3' },
});
