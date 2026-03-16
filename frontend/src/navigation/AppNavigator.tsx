/**
 * 앱 네비게이션 구조 (역할별 분기)
 * - 비로그인: LoginScreen
 * - admin: AdminDashboard (프로그램 관리자 뷰)
 * - manager: ManagerDashboard + 상품관리 탭들
 * - customer: 기존 Bottom Tabs (홈, 검색, 장바구니, 경로, AI, 프로필)
 * - SafeAreaProvider로 전체 앱 감싸서 상/하단 시스템 바 침범 방지
 */
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { useAuthStore } from '../store/authStore';
import LoginScreen from '../screens/LoginScreen';
import HomeScreen from '../screens/HomeScreen';
import ProductSearchScreen from '../screens/ProductSearchScreen';
import CartScreen from '../screens/CartScreen';
import RouteMapScreen from '../screens/RouteMapScreen';
import AIChatScreen from '../screens/AIChatScreen';
import ProfileScreen from '../screens/ProfileScreen';
import AdminDashboardScreen from '../screens/AdminDashboardScreen';
import ManagerDashboardScreen from '../screens/ManagerDashboardScreen';
import MapEditorScreen from '../screens/MapEditorScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();
const SearchStack = createNativeStackNavigator();
const RouteStack = createNativeStackNavigator();
const AdminTab = createBottomTabNavigator();
const ManagerTab = createBottomTabNavigator();

// ──────────── 일반 사용자(customer) 탭 ────────────
function SearchStackScreen() {
  return (
    <SearchStack.Navigator screenOptions={{ headerShown: false }}>
      <SearchStack.Screen name="ProductSearch" component={ProductSearchScreen} />
    </SearchStack.Navigator>
  );
}

function RouteStackScreen() {
  return (
    <RouteStack.Navigator screenOptions={{ headerShown: false }}>
      <RouteStack.Screen name="RouteMap" component={RouteMapScreen} />
    </RouteStack.Navigator>
  );
}

function CustomerTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused }) => {
          let icon = '';
          switch (route.name) {
            case 'HomeTab': icon = '🏠'; break;
            case 'SearchTab': icon = '🔍'; break;
            case 'CartTab': icon = '🛒'; break;
            case 'RouteTab': icon = '🗺️'; break;
            case 'AITab': icon = '🤖'; break;
            case 'ProfileTab': icon = '👤'; break;
          }
          return <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.5 }}>{icon}</Text>;
        },
        tabBarLabelStyle: { fontSize: 10, marginTop: -4 },
        tabBarActiveTintColor: '#0984e3',
        tabBarInactiveTintColor: '#b2bec3',
        tabBarStyle: { paddingBottom: 4, height: 56 },
      })}
    >
      <Tab.Screen name="HomeTab" component={HomeScreen} options={{ title: '홈' }} />
      <Tab.Screen name="SearchTab" component={SearchStackScreen} options={{ title: '검색' }} />
      <Tab.Screen name="CartTab" component={CartScreen} options={{ title: '장바구니' }} />
      <Tab.Screen name="RouteTab" component={RouteStackScreen} options={{ title: '경로' }} />
      <Tab.Screen name="AITab" component={AIChatScreen} options={{ title: 'AI' }} />
      <Tab.Screen name="ProfileTab" component={ProfileScreen} options={{ title: '내 정보' }} />
    </Tab.Navigator>
  );
}

// ──────────── 프로그램 관리자(admin) 탭 ────────────
function AdminTabs() {
  return (
    <AdminTab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused }) => {
          let icon = '';
          switch (route.name) {
            case 'DashboardTab': icon = '📊'; break;
            case 'StoreSearchTab': icon = '🔍'; break;
            case 'MapEditorTab': icon = '✏️'; break;
            case 'ProfileTab': icon = '👤'; break;
          }
          return <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.5 }}>{icon}</Text>;
        },
        tabBarLabelStyle: { fontSize: 10, marginTop: -4 },
        tabBarActiveTintColor: '#d63031',
        tabBarInactiveTintColor: '#b2bec3',
        tabBarStyle: { paddingBottom: 4, height: 56 },
      })}
    >
      <AdminTab.Screen name="DashboardTab" component={AdminDashboardScreen} options={{ title: '대시보드' }} />
      <AdminTab.Screen name="StoreSearchTab" component={SearchStackScreen} options={{ title: '상품 조회' }} />
      <AdminTab.Screen name="MapEditorTab" component={MapEditorScreen} options={{ title: '지도 편집' }} />
      <AdminTab.Screen name="ProfileTab" component={ProfileScreen} options={{ title: '내 정보' }} />
    </AdminTab.Navigator>
  );
}

// ──────────── 마트 관리자(manager) 탭 ────────────
function ManagerTabs() {
  return (
    <ManagerTab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused }) => {
          let icon = '';
          switch (route.name) {
            case 'DashboardTab': icon = '📊'; break;
            case 'ProductTab': icon = '📦'; break;
            case 'MapTab': icon = '🗺️'; break;
            case 'ProfileTab': icon = '👤'; break;
          }
          return <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.5 }}>{icon}</Text>;
        },
        tabBarLabelStyle: { fontSize: 10, marginTop: -4 },
        tabBarActiveTintColor: '#e17055',
        tabBarInactiveTintColor: '#b2bec3',
        tabBarStyle: { paddingBottom: 4, height: 56 },
      })}
    >
      <ManagerTab.Screen name="DashboardTab" component={ManagerDashboardScreen} options={{ title: '대시보드' }} />
      <ManagerTab.Screen name="ProductTab" component={SearchStackScreen} options={{ title: '상품 관리' }} />
      <ManagerTab.Screen name="MapTab" component={RouteStackScreen} options={{ title: '매장 지도' }} />
      <ManagerTab.Screen name="ProfileTab" component={ProfileScreen} options={{ title: '내 정보' }} />
    </ManagerTab.Navigator>
  );
}

// ──────────── 역할별 메인 화면 선택 ────────────
function getMainComponent(role?: string) {
  switch (role) {
    case 'admin': return AdminTabs;
    case 'manager': return ManagerTabs;
    default: return CustomerTabs;
  }
}

export default function AppNavigator() {
  const { token, user, loadToken } = useAuthStore();

  useEffect(() => {
    loadToken();
  }, []);

  const MainComponent = getMainComponent(user?.role);

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {token ? (
            <Stack.Screen name="Main" component={MainComponent} />
          ) : (
            <Stack.Screen name="Login" component={LoginScreen} />
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
