import { useMemo, useState } from "react";

import { Button, Divider, Group, Stack } from "@mantine/core";
import { DataTable } from "mantine-datatable";

import { useNotifications } from "../../api/hooks/system";

const PAGE_SIZES = [10, 15, 20];

function NotificationsPage() {
  const { data: notifications = [], refetch } = useNotifications();
  const [pageSize, setPageSize] = useState(PAGE_SIZES[1]);
  const [page, setPage] = useState(1);

  const records = useMemo(() => {
    const from = (page - 1) * pageSize;
    return notifications.slice(from, from + pageSize);
  }, [notifications, page, pageSize]);

  const refreshNotifications = () => {
    refetch();
  };

  return (
    <Stack>
      <Group>
        {/* TODO: Replace with icon
                  Add Filters */}
        <Button onClick={refreshNotifications}>Refresh Notifications</Button>
      </Group>
      <Divider />
      <DataTable
        records={records}
        columns={[
          { accessor: "type", title: "Type" },
          { accessor: "message", title: "Message" },
          { accessor: "timestamp", title: "Timestamp" },
        ]}
        totalRecords={notifications.length}
        recordsPerPage={pageSize}
        page={page}
        onPageChange={(p) => setPage(p)}
        recordsPerPageOptions={PAGE_SIZES}
        onRecordsPerPageChange={setPageSize}
      />
    </Stack>
  );
}

export default NotificationsPage;
