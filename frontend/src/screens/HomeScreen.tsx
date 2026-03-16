/**
 * 홈 화면 - 매장 정보, 빠른 메뉴, 오늘의 행사 상품
 * SafeArea 적용 + 행사 상품(할인) 표시 + 장바구니 담기
 */
import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  RefreshControl, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore } from '../store/authStore';
import { useCartStore } from '../store/cartStore';
import { productAPI } from '../services/api';
import { DEFAULT_STORE_ID, DEFAULT_STORE_NAME } from '../store/storeConfig';

export default function HomeScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const { user } = useAuthStore();
  const { itemCount, fetchCart, addItem } = useCartStore();
  const [products, setProducts] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const res = await productAPI.search({ page: 1, size: 6, store_id: DEFAULT_STORE_ID });
      setProducts(res.data.items || []);
    } catch {}
  };

  useEffect(() => {
    loadData();
    fetchCart();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    await fetchCart();
    setRefreshing(false);
  };

  const handleAddToCart = async (productId: string, productName: string) => {
    const ok = await addItem(productId);
    if (ok) {
      Alert.alert('추가 완료', `${productName}을(를) 장바구니에 담았습니다`);
    }
  };

  const getCategoryEmoji = (categoryId: number) => {
    if (categoryId <= 4) return '🥩';
    if (categoryId === 5) return '🥛';
    if (categoryId === 6) return '🥬';
    if (categoryId === 7) return '🧂';
    if (categoryId === 8) return '🍺';
    if (categoryId === 9) return '🍪';
    return '📦';
  };

  // 행사(할인) 상품 여부 확인
  const isSaleProduct = (product: any) => {
    return product.sale_price && product.sale_price > 0 && product.sale_price < product.regular_price;
  };

  // 할인율 계산
  const getDiscountRate = (product: any) => {
    if (!isSaleProduct(product)) return 0;
    return Math.round((1 - product.sale_price / product.regular_price) * 100);
  };

  return (
    <ScrollView
      style={[styles.container, { paddingTop: insets.top }]}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* 헤더 */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>안녕하세요, {user?.user_name || '고객'}님!</Text>
          <Text style={styles.storeName}>📍 {DEFAULT_STORE_NAME}</Text>
        </View>
        <TouchableOpacity
          style={styles.cartBadge}
          onPress={() => navigation.navigate('CartTab')}
        >
          <Text style={styles.cartIcon}>🛒</Text>
          {itemCount > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{itemCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* 빠른 메뉴 */}
      <View style={styles.quickMenu}>
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => navigation.navigate('SearchTab')}
        >
          <Text style={styles.menuIcon}>🔍</Text>
          <Text style={styles.menuLabel}>상품 검색</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => navigation.navigate('RouteTab')}
        >
          <Text style={styles.menuIcon}>🗺️</Text>
          <Text style={styles.menuLabel}>경로 안내</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => navigation.navigate('AITab')}
        >
          <Text style={styles.menuIcon}>🤖</Text>
          <Text style={styles.menuLabel}>AI 도우미</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => navigation.navigate('CartTab')}
        >
          <Text style={styles.menuIcon}>🛒</Text>
          <Text style={styles.menuLabel}>장바구니</Text>
        </TouchableOpacity>
      </View>

      {/* 오늘의 행사 상품 */}
      <Text style={styles.sectionTitle}>오늘의 행사 상품</Text>
      <View style={styles.productGrid}>
        {products.map((p: any) => (
          <View key={p.product_id} style={styles.productCard}>
            {/* 할인 배지 */}
            {isSaleProduct(p) && (
              <View style={styles.saleBadge}>
                <Text style={styles.saleBadgeText}>{getDiscountRate(p)}%</Text>
              </View>
            )}
            <Text style={styles.productEmoji}>
              {getCategoryEmoji(p.category_id)}
            </Text>
            <Text style={styles.productName} numberOfLines={1}>{p.product_name}</Text>
            {/* 가격 표시 */}
            {isSaleProduct(p) ? (
              <View style={styles.priceContainer}>
                <Text style={styles.originalPrice}>
                  {p.regular_price?.toLocaleString()}원
                </Text>
                <Text style={styles.salePrice}>
                  {p.sale_price?.toLocaleString()}원
                </Text>
              </View>
            ) : p.regular_price ? (
              <Text style={styles.regularPrice}>
                {p.regular_price?.toLocaleString()}원
              </Text>
            ) : (
              <Text style={styles.productSpec}>{p.specification || ''}</Text>
            )}
            {/* 장바구니 담기 버튼 */}
            <TouchableOpacity
              style={styles.addCartBtn}
              onPress={() => handleAddToCart(p.product_id, p.product_name)}
            >
              <Text style={styles.addCartBtnText}>담기</Text>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      {/* 하단 여백 */}
      <View style={{ height: 20 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingTop: 16, paddingBottom: 12,
    backgroundColor: '#0984e3',
  },
  greeting: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  storeName: { color: '#dfe6e9', fontSize: 13, marginTop: 2 },
  cartBadge: { position: 'relative', padding: 8 },
  cartIcon: { fontSize: 28 },
  badge: {
    position: 'absolute', top: 2, right: 0,
    backgroundColor: '#d63031', borderRadius: 10,
    minWidth: 20, height: 20, alignItems: 'center', justifyContent: 'center',
  },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  quickMenu: {
    flexDirection: 'row', justifyContent: 'space-around',
    paddingVertical: 20, paddingHorizontal: 16,
    backgroundColor: '#fff', marginBottom: 8,
  },
  menuItem: { alignItems: 'center', gap: 6 },
  menuIcon: { fontSize: 32 },
  menuLabel: { fontSize: 12, color: '#2d3436', fontWeight: '600' },
  sectionTitle: {
    fontSize: 18, fontWeight: 'bold', color: '#2d3436',
    paddingHorizontal: 20, paddingVertical: 12,
  },
  productGrid: {
    flexDirection: 'row', flexWrap: 'wrap',
    paddingHorizontal: 12, gap: 8,
  },
  productCard: {
    width: '30%', backgroundColor: '#fff', borderRadius: 12,
    padding: 12, alignItems: 'center', position: 'relative',
    shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
  },
  saleBadge: {
    position: 'absolute', top: 6, left: 6,
    backgroundColor: '#d63031', borderRadius: 8,
    paddingHorizontal: 6, paddingVertical: 2,
  },
  saleBadgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
  productEmoji: { fontSize: 36, marginBottom: 6 },
  productName: { fontSize: 13, fontWeight: '600', color: '#2d3436', textAlign: 'center' },
  productSpec: { fontSize: 11, color: '#636e72', marginTop: 2 },
  priceContainer: { alignItems: 'center', marginTop: 4 },
  originalPrice: {
    fontSize: 11, color: '#b2bec3',
    textDecorationLine: 'line-through',
  },
  salePrice: { fontSize: 13, fontWeight: 'bold', color: '#d63031' },
  regularPrice: { fontSize: 12, fontWeight: '600', color: '#0984e3', marginTop: 2 },
  addCartBtn: {
    marginTop: 8, backgroundColor: '#0984e3', borderRadius: 8,
    paddingHorizontal: 14, paddingVertical: 5,
  },
  addCartBtnText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
});
