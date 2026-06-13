import { SafeAreaView } from "react-native-safe-area-context";
import { Text, View } from "react-native";

export default function AccountScreen() {
  return (
    <SafeAreaView edges={["bottom"]} className="flex-1 bg-base">
      <View className="flex-1 items-center justify-center px-6">
        <Text className="font-display text-2xl text-ink">Account</Text>
        <Text className="mt-2 text-center font-sans text-sm text-ink-muted">
          Sign up and log in arrive in the next wave.
        </Text>
      </View>
    </SafeAreaView>
  );
}
