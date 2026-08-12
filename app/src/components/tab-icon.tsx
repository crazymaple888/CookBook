import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, View } from 'react-native';

type TabIconProps = {
  name: keyof typeof Ionicons.glyphMap;
  label: string;
  color: string;
  focused: boolean;
};

export function TabIcon({ name, label, color, focused }: TabIconProps) {
  return (
    <View style={styles.container}>
      <Ionicons name={name} size={20} color={color} />
      <Text style={[styles.label, focused && styles.labelActive, { color }]}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  label: {
    fontSize: 10,
    marginTop: 2,
    lineHeight: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  labelActive: {
    fontWeight: '700',
  },
});
