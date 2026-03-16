/**
 * 로그인 / 회원가입 화면
 * 역할별 계정: 이메일 도메인으로 자동 구분
 *  - @admin.smartmart.com → 프로그램 관리자
 *  - @manager.smartmart.com → 마트 관리자
 *  - 그 외 → 일반 사용자
 */
import React, { useState, useMemo } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Alert, KeyboardAvoidingView, Platform, ActivityIndicator,
  ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore, getRoleFromEmail, getRoleLabel } from '../store/authStore';

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userName, setUserName] = useState('');
  const [showRoleGuide, setShowRoleGuide] = useState(false);

  const { login, register, isLoading, error, clearError } = useAuthStore();

  // 현재 입력된 이메일로 역할 미리보기
  const detectedRole = useMemo(() => {
    if (!email.includes('@')) return null;
    return getRoleFromEmail(email);
  }, [email]);

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('알림', '이메일과 비밀번호를 입력해주세요');
      return;
    }

    if (isRegister) {
      if (!userName.trim()) {
        Alert.alert('알림', '이름을 입력해주세요');
        return;
      }
      const role = getRoleFromEmail(email);
      const roleLabel = getRoleLabel(role);
      const ok = await register(email, password, userName);
      if (ok) {
        Alert.alert('성공', `회원가입 완료! (${roleLabel})\n로그인해주세요`);
        setIsRegister(false);
      }
    } else {
      await login(email, password);
    }
  };

  // 빠른 로그인 (데모용 프리셋)
  const quickFill = (presetEmail: string) => {
    setEmail(presetEmail);
    setPassword('demo1234');
    if (isRegister) {
      const role = getRoleFromEmail(presetEmail);
      setUserName(role === 'admin' ? '시스템관리자' : role === 'manager' ? '매장관리자' : '홍길동');
    }
  };

  React.useEffect(() => {
    if (error) {
      Alert.alert('오류', error);
      clearError();
    }
  }, [error]);

  return (
    <KeyboardAvoidingView
      style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.logo}>🛒</Text>
          <Text style={styles.title}>스마트마트</Text>
          <Text style={styles.subtitle}>최적 경로 추천 쇼핑 앱</Text>
        </View>

        <View style={styles.form}>
          {isRegister && (
            <TextInput
              style={styles.input}
              placeholder="이름"
              value={userName}
              onChangeText={setUserName}
              autoCapitalize="none"
            />
          )}
          <TextInput
            style={styles.input}
            placeholder="이메일"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          {/* 역할 감지 표시 */}
          {detectedRole && (
            <View style={[styles.roleBadge, {
              backgroundColor: detectedRole === 'admin' ? '#d63031' :
                               detectedRole === 'manager' ? '#e17055' : '#00b894',
            }]}>
              <Text style={styles.roleBadgeText}>
                {getRoleLabel(detectedRole)} 계정으로 {isRegister ? '가입' : '로그인'}됩니다
              </Text>
            </View>
          )}

          <TextInput
            style={styles.input}
            placeholder="비밀번호 (6자 이상)"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <TouchableOpacity
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={handleSubmit}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>
                {isRegister ? '회원가입' : '로그인'}
              </Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.switchButton}
            onPress={() => setIsRegister(!isRegister)}
          >
            <Text style={styles.switchText}>
              {isRegister ? '이미 계정이 있으신가요? 로그인' : '계정이 없으신가요? 회원가입'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* 역할 안내 + 빠른 입력 */}
        <TouchableOpacity
          style={styles.guideToggle}
          onPress={() => setShowRoleGuide(!showRoleGuide)}
        >
          <Text style={styles.guideToggleText}>
            {showRoleGuide ? '▲ 계정 역할 안내 접기' : '▼ 계정 역할 안내 보기'}
          </Text>
        </TouchableOpacity>

        {showRoleGuide && (
          <View style={styles.roleGuide}>
            <Text style={styles.guideTitle}>이메일 도메인에 따라 역할이 자동 결정됩니다</Text>

            <TouchableOpacity
              style={[styles.roleRow, { borderLeftColor: '#d63031' }]}
              onPress={() => quickFill('admin@admin.smartmart.com')}
            >
              <View style={[styles.roleDot, { backgroundColor: '#d63031' }]} />
              <View style={styles.roleInfo}>
                <Text style={styles.roleName}>프로그램 관리자</Text>
                <Text style={styles.roleEmail}>@admin.smartmart.com</Text>
                <Text style={styles.roleDesc}>전체 시스템 관리, 매장 등록, IoT 대시보드</Text>
              </View>
              <Text style={styles.quickFillText}>입력</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.roleRow, { borderLeftColor: '#e17055' }]}
              onPress={() => quickFill('mart@manager.smartmart.com')}
            >
              <View style={[styles.roleDot, { backgroundColor: '#e17055' }]} />
              <View style={styles.roleInfo}>
                <Text style={styles.roleName}>마트 관리자</Text>
                <Text style={styles.roleEmail}>@manager.smartmart.com</Text>
                <Text style={styles.roleDesc}>상품/가격 관리, ESL 업데이트, 혼잡도 관리</Text>
              </View>
              <Text style={styles.quickFillText}>입력</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.roleRow, { borderLeftColor: '#00b894' }]}
              onPress={() => quickFill('user@gmail.com')}
            >
              <View style={[styles.roleDot, { backgroundColor: '#00b894' }]} />
              <View style={styles.roleInfo}>
                <Text style={styles.roleName}>일반 사용자</Text>
                <Text style={styles.roleEmail}>일반 이메일 (예: @gmail.com)</Text>
                <Text style={styles.roleDesc}>쇼핑, 경로 안내, AI 도우미, 장바구니</Text>
              </View>
              <Text style={styles.quickFillText}>입력</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingBottom: 30,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: { fontSize: 64, marginBottom: 8 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#2d3436' },
  subtitle: { fontSize: 14, color: '#636e72', marginTop: 4 },
  form: { gap: 12 },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1, borderColor: '#dfe6e9', borderRadius: 12,
    paddingHorizontal: 16, paddingVertical: 14, fontSize: 16,
  },
  roleBadge: {
    borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8,
    alignItems: 'center',
  },
  roleBadgeText: { color: '#fff', fontSize: 13, fontWeight: '600' },
  button: {
    backgroundColor: '#0984e3', borderRadius: 12,
    paddingVertical: 16, alignItems: 'center', marginTop: 8,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  switchButton: { alignItems: 'center', marginTop: 16 },
  switchText: { color: '#0984e3', fontSize: 14 },

  // 역할 안내
  guideToggle: { alignItems: 'center', marginTop: 24 },
  guideToggleText: { color: '#636e72', fontSize: 13 },
  roleGuide: {
    marginTop: 12, backgroundColor: '#fff', borderRadius: 12,
    padding: 16, gap: 12,
  },
  guideTitle: { fontSize: 13, color: '#636e72', textAlign: 'center', marginBottom: 4 },
  roleRow: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#f8f9fa', borderRadius: 10, padding: 12,
    borderLeftWidth: 4, gap: 10,
  },
  roleDot: { width: 12, height: 12, borderRadius: 6 },
  roleInfo: { flex: 1 },
  roleName: { fontSize: 14, fontWeight: 'bold', color: '#2d3436' },
  roleEmail: { fontSize: 12, color: '#0984e3', marginTop: 2 },
  roleDesc: { fontSize: 11, color: '#636e72', marginTop: 2 },
  quickFillText: {
    color: '#0984e3', fontSize: 12, fontWeight: 'bold',
    backgroundColor: '#dfe6e920', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6,
  },
});
