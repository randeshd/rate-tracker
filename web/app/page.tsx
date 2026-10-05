import Dashboard from "./Dashboard";
import { loadData } from "@/lib/data";

export default function Home() {
  return <Dashboard data={loadData()} />;
}
