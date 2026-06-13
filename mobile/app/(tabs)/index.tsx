import { SafeAreaView } from "react-native-safe-area-context";
import { Text, View } from "react-native";

export default function DiscoverScreen() {
  return (
    <SafeAreaView edges={["bottom"]} className="flex-1 bg-base">
      <View className="flex-1 items-center justify-center px-6">
        <View className="w-full rounded-2xl border border-border bg-surface p-6">
          <Text className="font-display text-3xl text-primary">Chuckwagon</Text>
          <Text className="mt-1 font-sans text-base text-ink">
            Find food trucks near you.
          </Text>
          <View className="mt-4 self-start rounded-full bg-status-here px-3 py-1">
            <Text className="font-sans-semibold text-xs text-surface">
              ● Skeleton is live
            </Text>
          </View>
          <Text className="mt-4 font-sans text-sm text-ink-muted">
            Next: the nearby live/soon list with your real location, wired to the
            discovery API.
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}
