import { SafeAreaView } from "react-native-safe-area-context";
import { Text, View } from "react-native";

export default function FollowingScreen() {
  return (
    <SafeAreaView edges={["bottom"]} className="flex-1 bg-base">
      <View className="flex-1 items-center justify-center px-6">
        <Text className="font-display text-2xl text-ink">Following</Text>
        <Text className="mt-2 text-center font-sans text-sm text-ink-muted">
          Trucks you follow will live here once accounts and follow are wired up.
        </Text>
      </View>
    </SafeAreaView>
  );
}
