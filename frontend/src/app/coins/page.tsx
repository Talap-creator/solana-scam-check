import { CoinsFeed } from "@/components/coins-feed";

type CoinsPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CoinsPage({ searchParams }: CoinsPageProps) {
  const resolved = searchParams ? await searchParams : {};

  return <CoinsFeed initialSearchParams={resolved} />;
}
