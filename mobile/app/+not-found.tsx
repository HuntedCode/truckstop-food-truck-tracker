import { Link, Stack } from "expo-router";
import { Text, View } from "react-native";

export default function NotFoundScreen() {
  return (
    <>
      <Stack.Screen options={{ title: "Not found" }} />
      <View className="flex-1 items-center justify-center bg-base px-6">
        <Text className="font-display text-2xl text-ink">Nothing here</Text>
        <Link href="/" className="mt-3 font-sans-semibold text-base text-primary">
          Back to Discover
        </Link>
      </View>
    </>
  );
}
