/**
 * AI 쇼핑 도우미 채팅 화면
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity,
  StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { aiAPI } from '../services/api';
import { useCartStore } from '../store/cartStore';
import { DEFAULT_STORE_ID } from '../store/storeConfig';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  recommendations?: any[];
  cartUpdates?: any[];
}

export default function AIChatScreen() {
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content: '안녕하세요! 스마트마트 쇼핑 도우미입니다. 🛒\n\n상품 검색, 레시피 추천, 장바구니 관리를 도와드릴게요.\n\n예시:\n• "삼겹살 파티 레시피 추천해줘"\n• "우유 찾아줘"\n• "삼겹살이랑 뭐 같이 먹으면 좋아?"',
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  const { fetchCart } = useCartStore();

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const res = await aiAPI.chat({ message: text, store_id: DEFAULT_STORE_ID });
      const data = res.data.data;

      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.message,
        recommendations: data.recommendations,
        cartUpdates: data.cart_updates,
      };
      setMessages((prev) => [...prev, aiMsg]);

      // 장바구니 변경 시 새로고침
      if (data.cart_updates?.length > 0) {
        await fetchCart();
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '죄송해요, 오류가 발생했어요. 다시 시도해주세요.',
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    // 새 메시지 시 스크롤
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  const renderMessage = ({ item }: { item: ChatMessage }) => {
    const isUser = item.role === 'user';
    return (
      <View style={[styles.msgRow, isUser && styles.msgRowUser]}>
        {!isUser && <Text style={styles.avatar}>🤖</Text>}
        <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAI]}>
          <Text style={[styles.msgText, isUser && styles.msgTextUser]}>
            {item.content}
          </Text>
          {/* 추천 상품 태그 */}
          {item.recommendations && item.recommendations.length > 0 && (
            <View style={styles.tags}>
              {item.recommendations.slice(0, 4).map((rec: any, idx: number) => (
                <View key={idx} style={styles.tag}>
                  <Text style={styles.tagText}>{rec.product_name}</Text>
                </View>
              ))}
            </View>
          )}
          {/* 장바구니 업데이트 알림 */}
          {item.cartUpdates && item.cartUpdates.length > 0 && (
            <View style={styles.cartAlert}>
              <Text style={styles.cartAlertText}>
                🛒 장바구니에 {item.cartUpdates.length}개 상품 추가됨
              </Text>
            </View>
          )}
        </View>
        {isUser && <Text style={styles.avatar}>👤</Text>}
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.chatList}
      />

      {/* 빠른 질문 버튼 */}
      {messages.length <= 1 && (
        <View style={styles.quickQuestions}>
          {['삼겹살 파티 레시피', '우유 찾아줘', '장바구니 보여줘'].map((q) => (
            <TouchableOpacity
              key={q}
              style={styles.quickBtn}
              onPress={() => { setInput(q); }}
            >
              <Text style={styles.quickBtnText}>{q}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* 입력 바 */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.textInput}
          placeholder="메시지를 입력하세요..."
          value={input}
          onChangeText={setInput}
          onSubmitEditing={handleSend}
          returnKeyType="send"
          editable={!sending}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!input.trim() || sending) && styles.sendDisabled]}
          onPress={handleSend}
          disabled={!input.trim() || sending}
        >
          {sending ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.sendText}>전송</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  chatList: { paddingHorizontal: 12, paddingVertical: 8 },
  msgRow: { flexDirection: 'row', marginBottom: 10, alignItems: 'flex-end' },
  msgRowUser: { justifyContent: 'flex-end' },
  avatar: { fontSize: 24, marginHorizontal: 4 },
  bubble: {
    maxWidth: '75%', borderRadius: 16, paddingHorizontal: 14, paddingVertical: 10,
  },
  bubbleAI: { backgroundColor: '#fff', borderBottomLeftRadius: 4 },
  bubbleUser: { backgroundColor: '#0984e3', borderBottomRightRadius: 4 },
  msgText: { fontSize: 14, lineHeight: 20, color: '#2d3436' },
  msgTextUser: { color: '#fff' },
  tags: {
    flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8,
  },
  tag: {
    backgroundColor: '#dfe6e9', borderRadius: 12,
    paddingHorizontal: 10, paddingVertical: 4,
  },
  tagText: { fontSize: 11, color: '#2d3436' },
  cartAlert: {
    marginTop: 8, backgroundColor: '#00b89422',
    borderRadius: 8, padding: 6,
  },
  cartAlertText: { fontSize: 12, color: '#00b894' },
  quickQuestions: {
    flexDirection: 'row', justifyContent: 'center', gap: 8,
    paddingVertical: 8, paddingHorizontal: 12,
  },
  quickBtn: {
    backgroundColor: '#fff', borderRadius: 16,
    paddingHorizontal: 12, paddingVertical: 8,
    borderWidth: 1, borderColor: '#0984e3',
  },
  quickBtnText: { fontSize: 12, color: '#0984e3' },
  inputBar: {
    flexDirection: 'row', paddingHorizontal: 12, paddingVertical: 8,
    backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#dfe6e9',
    gap: 8,
  },
  textInput: {
    flex: 1, backgroundColor: '#f1f2f6', borderRadius: 20,
    paddingHorizontal: 16, paddingVertical: 10, fontSize: 15,
  },
  sendButton: {
    backgroundColor: '#0984e3', borderRadius: 20,
    paddingHorizontal: 18, justifyContent: 'center',
  },
  sendDisabled: { opacity: 0.5 },
  sendText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
});
