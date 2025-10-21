import { useEffect, useState } from "react";

import { Button, Divider, Group, Stack } from "@mantine/core";
import { DataTable } from "mantine-datatable";

import { getNotifications } from "../../api/api";
import type { Notification } from "../../api/ApiResponse";

function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    async function fetchNotifications() {
      const data = await getNotifications();
      setNotifications(data);
    }

    fetchNotifications();
  }, []);

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
        columns={[
          { accessor: "type", title: "Type" },
          { accessor: "message", title: "Message" },
          { accessor: "timestamp", title: "Timestamp" },
        ]}
        records={notifications}
      />
    </Stack>
  );
}

export default NotificationsPage;
