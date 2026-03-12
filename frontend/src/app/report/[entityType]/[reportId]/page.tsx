import { notFound } from "next/navigation";
import { ReportView } from "@/components/report-view";
import { ApiError, getCheckById } from "@/lib/api";

type ReportPageProps = {
  params: Promise<{
    entityType: string;
    reportId: string;
  }>;
};

export default async function ReportPage({ params }: ReportPageProps) {
  const { reportId } = await params;
  const report = await getCheckById(reportId).catch((error: unknown) => {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  });

  if (!report) {
    notFound();
  }

  return <ReportView report={report} />;
}
