import { useEffect, useState } from "react";

import { Button, Divider, Group, Stack } from "@mantine/core";
import { DataTable } from "mantine-datatable";

import { getNotifications } from "../../api/api";
import type { Notification } from "../../api/ApiResponse";

const PAGE_SIZES = [10, 15, 20];

function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [pageSize, setPageSize] = useState(PAGE_SIZES[1]);
  const [page, setPage] = useState(1);
  const [records, setRecords] = useState(notifications.slice(0, pageSize));

  useEffect(() => {
    async function fetchNotifications() {
      const data = await getNotifications();

      const sortedData = data.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      setNotifications(sortedData);
    }

    fetchNotifications();
  }, []);

  useEffect(() => {
    const from = (page - 1) * pageSize;
    const to = from + pageSize;
    setRecords(notifications.slice(from, to));
  }, [page, notifications, pageSize]);

  const refreshNotifications = async () => {
    const data = await getNotifications();
    setNotifications(data);
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
