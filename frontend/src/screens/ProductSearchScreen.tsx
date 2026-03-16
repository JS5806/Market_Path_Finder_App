/**
 * 상품 검색 화면 - SafeArea 적용 + 행사(할인) 라벨 표시
 */
import React, { useState, useCallback } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity,
  StyleSheet, ActivityIndicator, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { productAPI } from '../services/api';
import { useCartStore } from '../store/cartStore';
import { DEFAULT_STORE_ID } from '../store/storeConfig';

export default function ProductSearchScreen() {
  const insets = useSafeAreaInsets();
  const [keyword, setKeyword] = useState('');
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const { addItem } = useCartStore();

  const handleSearch = useCallback(async () => {
    if (!keyword.trim()) {
      // 전체 상품 조회
    }
    setLoading(true);
    try {
      const res = await productAPI.search({
        keyword: keyword.trim() || undefined,
        store_id: DEFAULT_STORE_ID,
        page: 1,
        size: 20,
      });
      setProducts(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch {
      Alert.alert('오류', '상품 검색에 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [keyword]);

  const handleAddToCart = async (productId: string, productName: string) => {
    const ok = await addItem(productId);
    if (ok) {
      Alert.alert('추가 완료', `${productName}을(를) 장바구니에 담았습니다`);
    }
  };

  // 초기 로드
  React.useEffect(() => {
    handleSearch();
  }, []);

  const getCategoryEmoji = (categoryId: number) => {
    if (categoryId <= 4) return '🥩';
    if (categoryId === 5) return '🥛';
    if (categoryId === 6) return '🥬';
    if (categoryId === 7) return '🧂';
    if (categoryId === 8) return '🍺';
    if (categoryId === 9) return '🍪';
    return '📦';
  };

  const isSaleProduct = (product: any) => {
    return product.sale_price && product.sale_price > 0 && product.sale_price < product.regular_price;
  };

  const getDiscountRate = (product: any) => {
    if (!isSaleProduct(product)) return 0;
    return Math.round((1 - product.sale_price / product.regular_price) * 100);
  };

  const renderProduct = ({ item }: { item: any }) => (
    <View style={styles.productCard}>
      <Text style={styles.emoji}>{getCategoryEmoji(item.category_id)}</Text>
      <View style={styles.productInfo}>
        <View style={styles.nameRow}>
          <Text style={styles.productName} numberOfLines={1}>{item.product_name}</Text>
          {isSaleProduct(item) && (
            <View style={styles.saleBadge}>
              <Text style={styles.saleBadgeText}>행사 {getDiscountRate(item)}%</Text>
            </View>
          )}
        </View>
        <Text style={styles.productSpec}>
          {item.manufacturer} | {item.specification}
        </Text>
        {/* 가격 표시 */}
        {isSaleProduct(item) ? (
          <View style={styles.priceRow}>
            <Text style={styles.originalPrice}>
              {item.regular_price?.toLocaleString()}원
            </Text>
            <Text style={styles.salePrice}>
              {item.sale_price?.toLocaleString()}원
            </Text>
          </View>
        ) : item.regular_price ? (
          <Text style={styles.regularPrice}>
            {item.regular_price?.toLocaleString()}원
          </Text>
        ) : null}
        {item.avg_rating > 0 && (
          <Text style={styles.rating}>⭐ {item.avg_rating}</Text>
        )}
      </View>
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => handleAddToCart(item.product_id, item.product_name)}
      >
        <Text style={styles.addButtonText}>담기</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* 검색바 */}
      <View style={styles.searchBar}>
        <TextInput
          style={styles.searchInput}
          placeholder="상품명, 브랜드 검색..."
          value={keyword}
          onChangeText={setKeyword}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
        />
        <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
          <Text style={styles.searchButtonText}>🔍</Text>
        </TouchableOpacity>
      </View>

      {/* 결과 수 */}
      <Text style={styles.resultCount}>검색 결과: {total}개</Text>

      {/* 상품 목록 */}
      {loading ? (
        <ActivityIndicator size="large" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={products}
          renderItem={renderProduct}
          keyExtractor={(item) => item.product_id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <Text style={styles.emptyText}>상품을 찾지 못했습니다</Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  searchBar: {
    flexDirection: 'row', paddingHorizontal: 16, paddingVertical: 12,
    backgroundColor: '#fff', gap: 8,
  },
  searchInput: {
    flex: 1, backgroundColor: '#f1f2f6', borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 10, fontSize: 15,
  },
  searchButton: {
    backgroundColor: '#0984e3', borderRadius: 10,
    paddingHorizontal: 16, justifyContent: 'center',
  },
  searchButtonText: { fontSize: 18 },
  resultCount: {
    paddingHorizontal: 16, paddingVertical: 8,
    fontSize: 13, color: '#636e72',
  },
  list: { paddingHorizontal: 16, paddingBottom: 20 },
  productCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#fff', borderRadius: 12, padding: 14,
    marginBottom: 8,
    shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 4, elevation: 1,
  },
  emoji: { fontSize: 36, marginRight: 12 },
  productInfo: { flex: 1 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  productName: { fontSize: 15, fontWeight: '600', color: '#2d3436', flexShrink: 1 },
  saleBadge: {
    backgroundColor: '#d63031', borderRadius: 6,
    paddingHorizontal: 6, paddingVertical: 2,
  },
  saleBadgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
  productSpec: { fontSize: 12, color: '#636e72', marginTop: 2 },
  priceRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 },
  originalPrice: {
    fontSize: 12, color: '#b2bec3',
    textDecorationLine: 'line-through',
  },
  salePrice: { fontSize: 14, fontWeight: 'bold', color: '#d63031' },
  regularPrice: { fontSize: 13, fontWeight: '600', color: '#0984e3', marginTop: 4 },
  rating: { fontSize: 12, color: '#fdcb6e', marginTop: 2 },
  addButton: {
    backgroundColor: '#0984e3', borderRadius: 8,
    paddingHorizontal: 14, paddingVertical: 8,
  },
  addButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 13 },
  emptyText: { textAlign: 'center', color: '#b2bec3', marginTop: 40, fontSize: 15 },
});
