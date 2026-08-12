import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarActiveTintColor: '#6fae97',
        tabBarInactiveTintColor: '#9aa0a6',
        tabBarLabelStyle: { fontSize: 12, lineHeight: 18, height: 18 },
        tabBarStyle: { height: 60, backgroundColor: '#14171a', borderTopColor: '#2a2f33' },
        headerTitleStyle: { fontWeight: '700', color: '#e8ece8' },
        headerStyle: { backgroundColor: '#171b18' },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: '首页',
          tabBarIcon: ({ color, size }) => <Ionicons name="restaurant" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="match"
        options={{
          title: '食材匹配',
          tabBarIcon: ({ color, size }) => <Ionicons name="search" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="community"
        options={{
          title: '社区',
          tabBarIcon: ({ color, size }) => <Ionicons name="people" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: '我的',
          tabBarIcon: ({ color, size }) => <Ionicons name="person" size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
